"""
Mass importer and matcher for agency uploads
"""

# Django
from django.core.validators import URLValidator, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

# Standard Library
import re

# Third Party
import unicodecsv as csv
from fuzzywuzzy import fuzz, process
from localflavor.us.us_states import STATE_CHOICES

# MuckRock
from muckrock.agency.models import (
    Agency,
    AgencyAddress,
    AgencyEmail,
    AgencyPhone,
    AgencyType,
)
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.communication.utils import validate_phone_number
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.portal.models import PORTAL_TYPES, Portal

STATES = [s[0] for s in STATE_CHOICES]
PORTALS = [p[0] for p in PORTAL_TYPES]


def valid_url(url):
    try:
        URLValidator(schemes=["http", "https"])(url)
        return True
    except ValidationError:
        return False


class CSVReader(object):
    def __init__(self, file_):
        self.csv_reader = csv.reader(file_)
        self.headers = next(self.csv_reader)

    def read(self):
        for row in self.csv_reader:
            yield dict(zip(self.headers, row))


class PyReader(object):
    def __init__(self, data):
        self.data = data

    def read(self):
        for datum in self.data:
            yield datum


class Writer(object):
    pass


class CSVWriter(Writer):
    pass


class Importer(object):

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
        return jurisdiction

    def _match_one(self, datum):
        jurisdiction = self._match_jurisdiction(datum)
        if jurisdiction is None:
            return datum

        agencies = Agency.objects.get_approved().filter(jurisdiction=jurisdiction)

        try:
            agency = agencies.get(name__iexact=datum["agency"])
            datum["match_agency"] = agency
            datum["agency_status"] = "exact match"
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
            datum["match_agency"] = agency
            datum["match_agency_score"] = score
            datum["agency_status"] = "fuzzy match"
        else:
            datum["agency_status"] = "no agency"

        return datum

    def _validate(self, datum):
        error = False
        if not datum.get("agency"):
            datum["agency_status"] = "missing agency"
            error = True
        if not datum.get("jurisdiction"):
            datum["jurisdiction_status"] = "missing jurisdiction"
            error = True
        return error

    def match(self):
        # first match jurisdiction
        # look for exact match
        # look for best fuzzy match
        for datum in self.data:
            error = self._validate(datum)
            if error:
                yield datum
            else:
                yield self._match_one(datum)

    def _create_agency(self, datum, user):
        agency = Agency.objects.create(
            name=datum["agency"],
            slug=(slugify(datum["agency"]) or "untitled"),
            jurisdiction=datum["match_jurisdiction"],
            status="approved",  # XXX option to make task?
            user=user,
        )
        datum["match_agency"] = agency
        datum["agency_status"] = "created"
        return agency

    def _import_email(self, agency, datum):
        email = datum.get("email")
        if email:
            email_address = EmailAddress.objects.fetch(email)
            if email_address is None:
                # email failed validation
                datum["email_status"] = "error"
                return
            if datum["agency_status"] == "created":
                # if the agency was just created, it does not have any existing emails
                request_type, email_type = "primary", "to"
                status = "primary"
            else:
                # otherwise check for existing email addresses
                if any(e == email_address for e in agency.emails.all()):
                    # email address is already present on the agency
                    datum["email_status"] = "already set"
                    return
                # check if it already has a primary email address
                if agency.get_emails("primary", "to"):  # optimize
                    request_type, email_type = "none", "none"
                    status = "other"
                else:
                    request_type, email_type = "primary", "to"
                    status = "primary"
            AgencyEmail.objects.create(
                agency=agency,
                email=email_address,
                request_type=request_type,
                email_type=email_type,
            )
            datum["email_status"] = "set {}".format(status)

    def _import_phone(self, agency, datum):
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
        fax = datum.get("fax")
        if fax:
            fax_number = PhoneNumber.objects.fetch(phone, type_="fax")
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
        aliases = datum.get("aliases")
        url = datum.get("foia_website")
        website = datum.get("website")
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
        if save:
            agency.save()

    def _import_one(self, datum, user):
        agency = datum.get("match_agency")
        if agency is None:
            agency = self._create_agency(datum, user)

        self._import_email(agency, datum)
        self._import_phone(agency, datum)
        self._import_fax(agency, datum)
        self._import_address(agency, datum)
        self._import_portal(agency, datum)
        self._import_other(agency, datum)

        return datum

    def import_(self, user=None, dry=False):
        with transaction.atomic():
            for datum in self.match():
                yield self._import_one(datum, user)
