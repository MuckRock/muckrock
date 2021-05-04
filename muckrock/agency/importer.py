"""
Mass importer and matcher for agency uploads
"""

# Django
from django.conf import settings
from django.core.validators import URLValidator, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

# Standard Library
import csv
import re

# Third Party
from fuzzywuzzy import fuzz, process
from localflavor.us.us_states import STATE_CHOICES

# MuckRock
from muckrock.agency.models import Agency, AgencyAddress, AgencyEmail, AgencyPhone
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.portal.models import PORTAL_TYPES, Portal

STATES = [s[0] for s in STATE_CHOICES]  # pylint: disable=not-an-iterable
PORTALS = [p[0] for p in PORTAL_TYPES]


def valid_url(url):
    """Return true for valid URLs"""
    try:
        URLValidator(schemes=["http", "https"])(url)
        return True
    except ValidationError:
        return False


class CSVReader:
    """Read the import data from a CSV file"""

    def __init__(self, file_):
        self.csv_reader = csv.reader(file_)
        self.headers = next(self.csv_reader)

    def read(self):
        """Create a dictionary from each CSV row by keying by the headers"""
        for row in self.csv_reader:
            yield dict(zip(self.headers, row))


class PyReader:
    """Read the import data from a python list of dictionaries
    Used for testing
    """

    def __init__(self, data):
        self.data = data

    def read(self):
        """Just iterate through the list"""
        for datum in self.data:
            yield datum


class Importer:
    """Match and import multiple agencies at a time"""

    p_zip = re.compile(r"^\d{5}(?:-\d{4})?$")

    def __init__(self, reader):
        self.data = reader.read()

    def _match_jurisdiction(self, datum):
        """Match the jurisdiction name"""
        jurisdiction_name = datum["jurisdiction"]
        # if there is a comma in the name, it is a locality state pair
        # seperate and try to find an exact match
        if "," in jurisdiction_name:
            locality, state = [j.strip() for j in jurisdiction_name.split(",", 1)]
            jurisdiction = Jurisdiction.objects.filter(
                Q(parent__name__iexact=state) | Q(parent__abbrev__iexact=state),
                name__iexact=locality,
                level="l",
            ).first()
        # otherwise assume it is a state or federal jurisdiction and just look
        # for an exact match
        else:
            name = jurisdiction_name.strip()
            jurisdiction = Jurisdiction.objects.filter(
                Q(name__iexact=name) | Q(abbrev__iexact=name), level__in=("s", "f")
            ).first()

        datum["match_jurisdiction"] = jurisdiction
        if jurisdiction is None:
            datum["jurisdiction_status"] = "no jurisdiction"
        else:
            datum["jurisdiction_status"] = "found"
        return jurisdiction

    def _set_match_agency(self, datum, agency, status, score=None):
        """Set match agency and related attributes for easy access"""
        datum["match_agency"] = agency
        datum["match_agency_url"] = settings.MUCKROCK_URL + agency.get_absolute_url()
        datum["match_agency_id"] = agency.pk
        datum["match_agency_name"] = agency.name
        datum["agency_status"] = status
        if score is not None:
            datum["match_agency_score"] = score

    def _match_one(self, datum):
        """Match a single agency"""
        jurisdiction = self._match_jurisdiction(datum)
        if jurisdiction is None:
            return datum

        agencies = Agency.objects.get_approved().filter(jurisdiction=jurisdiction)

        try:
            agency = agencies.get(name__iexact=datum["agency"])
            self._set_match_agency(datum, agency, "exact match")
            return datum
        except Agency.DoesNotExist:
            pass

        match = process.extractOne(
            datum["agency"],
            {a: a.name for a in agencies},
            scorer=fuzz.partial_ratio,
            score_cutoff=83,
        )
        if match:
            _agency_name, score, agency = match
            self._set_match_agency(datum, agency, "fuzzy match", score)
        else:
            datum["agency_status"] = "no agency"

        return datum

    def _validate(self, datum):
        """Validate the agency and jurisdiction information exist"""
        error = False
        if not datum.get("agency"):
            datum["agency_status"] = "missing agency"
            error = True
        if not datum.get("jurisdiction"):
            datum["jurisdiction_status"] = "missing jurisdiction"
            error = True
        return error

    def match(self):
        """Match each datum"""
        for datum in self.data:
            error = self._validate(datum)
            if error:
                yield datum
            else:
                yield self._match_one(datum)

    def _create_agency(self, datum, user):
        """Create an agency when importing a new agency"""
        agency = Agency.objects.create(
            name=datum["agency"],
            slug=(slugify(datum["agency"]) or "untitled"),
            jurisdiction=datum["match_jurisdiction"],
            status="approved",
            user=user,
        )
        self._set_match_agency(datum, agency, "created")
        return agency

    def _import_email(self, agency, datum):
        """Import an agency's email address"""
        email = datum.get("email")
        cc_emails = datum.get("cc_emails", "")
        if email:
            email_address = EmailAddress.objects.fetch(email)
            cc_email_addresses = EmailAddress.objects.fetch_many(cc_emails)
            if email_address is None:
                # email failed validation
                datum["email_status"] = "error"
                return
            if datum["agency_status"] == "created":
                # if the agency was just created, it does not have any existing emails
                request_type = "primary"
                email_type = "to"
                cc_type = "cc"
                status = "primary"
            else:
                # otherwise check for existing email addresses
                if any(e == email_address for e in agency.emails.all()):
                    # email address is already present on the agency
                    datum["email_status"] = "already set"
                    return
                # check if it already has a primary email address
                if agency.get_emails("primary", "to"):  # optimize
                    request_type = "none"
                    email_type = "none"
                    cc_type = "none"
                    status = "other"
                else:
                    request_type = "primary"
                    email_type = "to"
                    cc_type = "cc"
                    status = "primary"
            AgencyEmail.objects.create(
                agency=agency,
                email=email_address,
                request_type=request_type,
                email_type=email_type,
            )
            for cc_email_address in cc_email_addresses:
                AgencyEmail.objects.get_or_create(
                    agency=agency,
                    email=cc_email_address,
                    defaults={"request_type": request_type, "email_type": cc_type},
                )
            datum["email_status"] = "set {}".format(status)

    def _import_phone(self, agency, datum):
        """Import an agency's phone number"""
        phone = datum.get("phone")
        if phone:
            phone_number = PhoneNumber.objects.fetch(phone, type_="phone")
            if phone_number is None:
                datum["phone_status"] = "error"
                return
            _, created = AgencyPhone.objects.update_or_create(
                agency=agency, phone=phone_number
            )
            if created:
                datum["phone_status"] = "set"
            else:
                datum["phone_status"] = "already set"

    def _import_fax(self, agency, datum):
        """Import an agency's fax number"""
        fax = datum.get("fax")
        if fax:
            fax_number = PhoneNumber.objects.fetch(fax, type_="fax")
            if fax_number is None:
                datum["fax_status"] = "error"
                return
            if datum["agency_status"] == "created":
                request_type = "primary"
                status = "primary"
            else:
                if any(p == fax_number for p in agency.phones.filter(type="fax")):
                    # fax is already present on the agency
                    datum["fax_status"] = "already set"
                    return
                if agency.get_faxes("primary"):  # optimize
                    request_type = "none"
                    status = "other"
                else:
                    request_type = "primary"
                    status = "primary"
            AgencyPhone.objects.create(
                agency=agency, phone=fax_number, request_type=request_type
            )
            datum["fax_status"] = "set {}".format(status)

    def _import_address(self, agency, datum):
        """Import an agency's address"""
        address_parts = [
            "address_suite",
            "address_street",
            "address_city",
            "address_state",
            "address_zip",
        ]
        if any(p in datum for p in address_parts):
            suite = datum.get("address_suite", "")
            street = datum.get("address_street", "")
            city = datum.get("address_city", "")
            state = datum.get("address_state", "")
            zip_code = datum.get("address_zip", "")
            if not all(
                [
                    len(suite) <= 255,
                    len(street) <= 255,
                    len(city) <= 255,
                    state in STATES,
                    self.p_zip.match(zip_code),
                ]
            ):
                datum["address_status"] = "error"
                return
            address, _ = Address.objects.get_or_create(
                suite=datum.get("address_suite", ""),
                street=datum.get("address_street", ""),
                city=datum.get("address_city", ""),
                state=datum.get("address_state", ""),
                zip_code=datum.get("address_zip", ""),
            )
            if datum["agency_status"] == "created":
                request_type = "primary"
                status = "primary"
            else:
                if any(a == address for a in agency.addresses.all()):
                    # address is already present on the agency
                    datum["address_status"] = "already set"
                    return
                if agency.get_addresses("primary"):  # optimize
                    request_type = "none"
                    status = "other"
                else:
                    request_type = "primary"
                    status = "primary"
            AgencyAddress.objects.create(
                agency=agency, address=address, request_type=request_type
            )
            datum["address_status"] = "set {}".format(status)

    def _import_portal(self, agency, datum):
        """Import an agency's portal"""
        portal_url = datum.get("portal_url")
        portal_type = datum.get("portal_type")
        if portal_url and portal_type:
            if not valid_url(portal_url) or portal_type not in PORTALS:
                datum["portal_status"] = "error"
                return
            if agency.portal:
                datum["portal_status"] = "not set, existing"
                return
            portal, _ = Portal.objects.get_or_create(
                url=portal_url,
                defaults={
                    "type": portal_type,
                    "name": u"%s %s" % (agency, dict(PORTAL_TYPES)[portal_type]),
                },
            )
            agency.portal = portal
            agency.save()
            datum["portal_status"] = "set"

    def _import_other(self, agency, datum):
        """Import an agency's other information"""
        aliases = datum.get("aliases")
        url = datum.get("foia_website")
        website = datum.get("website")
        requires_proxy = datum.get("requires_proxy", "").lower()
        save = False
        if aliases and not agency.aliases:
            agency.aliases = aliases
            datum["aliases_status"] = "set"
            save = True
        if url and not agency.url:
            if not valid_url(url):
                datum["foia_website_status"] = "error"
            else:
                agency.url = url
                datum["foia_website_status"] = "set"
                save = True
        if website and not agency.website:
            if not valid_url(website):
                datum["website_status"] = "error"
            else:
                agency.website = website
                datum["website_status"] = "set"
                save = True
        if "requires_proxy" in datum:
            agency.requires_proxy = requires_proxy in ("t", "true", "y", "yes", "1")
            save = True
            datum["requires_proxy_status"] = "set {}".format(
                str(agency.requires_proxy).lower()
            )
        if save:
            agency.save()

    def _import_one(self, datum, user):
        """Import a single agency's data"""
        agency = datum.get("match_agency")
        if agency is None and datum.get("match_jurisdiction") is not None:
            agency = self._create_agency(datum, user)
        elif agency is None and datum.get("match_jurisdiction") is None:
            # no jurisdiction, cannot create new agency
            return datum

        self._import_email(agency, datum)
        self._import_phone(agency, datum)
        self._import_fax(agency, datum)
        self._import_address(agency, datum)
        self._import_portal(agency, datum)
        self._import_other(agency, datum)

        return datum

    def import_(self, user=None, dry=False):
        """Import all agency data"""
        with transaction.atomic():
            sid = transaction.savepoint()
            for datum in self.match():
                yield self._import_one(datum, user)
            if dry:
                transaction.savepoint_rollback(sid)
