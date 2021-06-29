# -*- coding: utf-8 -*-
"""
Models for keeping track of how we send and receive communications
"""

# Django
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.core.validators import validate_email
from django.db import models
from django.forms import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse

# Standard Library
from datetime import date
from email.utils import getaddresses, parseaddr

# Third Party
import phonenumbers
from localflavor.us.models import USStateField, USZipCodeField
from localflavor.us.us_states import STATE_CHOICES
from phonenumber_field.modelfields import PhoneNumberField

# MuckRock
from muckrock.mailgun.models import WhitelistDomain

PHONE_TYPES = (("fax", "Fax"), ("phone", "Phone"))
CHECK_STATUS = (
    ("pending", "Pending"),
    ("deposited", "Deposited"),
    ("returned", "Returned"),
    ("cancelled", "Cancelled"),
    ("lost", "Lost"),
)

# Address models


class EmailAddressQuerySet(models.QuerySet):
    """QuerySet for EmailAddresses"""

    def fetch(self, address):
        """Fetch an email address object based on an email header"""
        name, email = parseaddr(address)
        try:
            email = self._normalize_email(email)
        except ValidationError:
            return None
        email_address, _ = self.update_or_create(email=email, defaults={"name": name})
        return email_address

    def fetch_many(self, *addresses, **kwargs):
        """Fetch multiple email address objects based on an email header"""
        name_emails = getaddresses(addresses)
        addresses = []
        for name, email in name_emails:
            try:
                email = self._normalize_email(email)
            except ValidationError:
                if kwargs.get("ignore_errors", True):
                    continue
                else:
                    raise
            email_address, _ = self.update_or_create(
                email=email, defaults={"name": name}
            )
            addresses.append(email_address)
        return addresses

    @staticmethod
    def _normalize_email(email):
        """Username is case sensitive, domain is not"""
        # strip invisible spaces
        email = email.replace("\u200b", "")
        validate_email(email)
        username, domain = email.rsplit("@", 1)
        return "%s@%s" % (username, domain.lower())


class EmailAddress(models.Model):
    """An email address"""

    email = models.EmailField(unique=True)
    name = models.CharField(blank=True, max_length=255)
    status = models.CharField(
        max_length=5, choices=(("good", "Good"), ("error", "Error")), default="good"
    )

    objects = EmailAddressQuerySet.as_manager()

    def __str__(self):
        if self.name:
            val = '"%s" <%s>' % (self.name, self.email)
        else:
            val = self.email
        if self.status == "error":
            val += " (error)"
        return val

    def get_absolute_url(self):
        """The url for this email address"""
        return reverse("email-detail", kwargs={"idx": self.pk})

    @property
    def domain(self):
        """The domain part of the email address"""
        if "@" not in self.email:
            return ""
        return self.email.rsplit("@", 1)[1]

    def allowed(self, foia=None):
        """Is this email address allowed to post to this FOIA request?"""
        # pylint: disable=too-many-return-statements, import-outside-toplevel
        from muckrock.agency.models import AgencyEmail

        allowed_tlds = [
            ".%s.us" % a.lower()
            for (a, _) in list(STATE_CHOICES)
            if a not in ("AS", "DC", "GU", "MP", "PR", "VI")
        ]
        allowed_tlds.extend([".gov", ".mil"])

        # from the same domain as the FOIA email
        if foia and foia.email and self.domain == foia.email.domain:
            return True

        # the email is a known email for this FOIA's agency
        if foia and self.agencies.filter(pk=foia.agency_id).exists():
            return True

        # the email is a known email for this FOIA
        if foia and foia.cc_emails.filter(email=self).exists():
            return True

        # it is from any known government TLD
        if any(self.email.endswith(tld) for tld in allowed_tlds):
            return True

        # if not associated with any FOIA,
        # checked if the email is known for any agency
        if not foia and AgencyEmail.objects.filter(email=self).exists():
            return True

        # check the email domain against the whitelist
        if WhitelistDomain.objects.filter(domain__iexact=self.domain).exists():
            return True

        return False

    class Meta:
        verbose_name_plural = "email addresses"


class PhoneNumberQuerySet(models.QuerySet):
    """QuerySet for PhoneNumner"""

    def fetch(self, number, type_="fax"):
        """Fetch a number from the database, or create it if it doesn't exist"""
        try:
            number = phonenumbers.parse(number, "US")
            if not phonenumbers.is_valid_number(number):
                return None
            phone, _ = self.update_or_create(number=number, defaults={"type": type_})
            return phone
        except phonenumbers.NumberParseException:
            return None


class PhoneNumber(models.Model):
    """A phone number"""

    number = PhoneNumberField(unique=True)
    type = models.CharField(max_length=5, choices=PHONE_TYPES, default="phone")
    status = models.CharField(
        max_length=5, choices=(("good", "Good"), ("error", "Error")), default="good"
    )

    objects = PhoneNumberQuerySet.as_manager()

    def __str__(self):
        number = f"{self.number.as_national} ({self.type})"
        if self.status == "error":
            return f"{number} ({self.status})"
        else:
            return number

    def get_absolute_url(self):
        """The url for this phone number"""
        return reverse("phone-detail", kwargs={"idx": self.pk})

    @property
    def as_e164(self):
        """Format as E164 (suitable for phaxio)"""
        return self.number.as_e164


class Address(models.Model):
    """A mailing address"""

    # These fields are the components of a normal address
    street = models.CharField(blank=True, max_length=255)
    suite = models.CharField(blank=True, max_length=255)
    city = models.CharField(blank=True, max_length=255)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)

    # These are override fields for parts of the address
    agency_override = models.CharField(
        blank=True, max_length=255, help_text="Override the agency this is addressed to"
    )
    attn_override = models.CharField(
        blank=True,
        max_length=255,
        help_text="Override the attention line to address "
        "this to a particular person",
    )

    # This will become the override field for non-conforming addresses
    address = models.TextField(blank=True)

    def __str__(self):
        if self.zip_code:
            address = "{}, {} {}".format(self.city, self.state, self.zip_code)
            parts = [
                self.agency_override,
                self.attn_override,
                self.street,
                self.suite,
                address,
            ]
            address = ", ".join(p for p in parts if p)
            return address
        else:
            return self.address

    def format(self, agency, appeal=False):
        """Format an address for mailing"""
        # if we do not have address components use the
        # full address override
        if not self.zip_code:
            return self.address

        # otherwise we build the address line by line
        address = []
        # agency addressed to
        if self.agency_override:
            address.append(self.agency_override)
        else:
            address.append(agency.name)
        # ATTN line
        if self.attn_override:
            address.append(self.attn_override)
        else:
            if appeal:
                office = "Appeal"
            else:
                office = "Office"
            address.append(
                "{} {}".format(agency.jurisdiction.get_law_name(abbrev=True), office)
            )
        if self.suite:
            address.append(self.suite)
        if self.street:
            address.append(self.street)
        address.append("{}, {} {}".format(self.city, self.state, self.zip_code))
        return "\n".join(address)

    def lob_format(self, agency):
        """Format an address for use with Lob"""
        lob = {}
        if self.agency_override and len(self.agency_override) < 40:
            lob["name"] = self.agency_override
        elif agency.mail_name:
            lob["name"] = agency.mail_name
        else:
            lob["name"] = agency.name
        if self.attn_override:
            lob["company"] = self.attn_override
        else:
            lob["company"] = "{} Office".format(
                agency.jurisdiction.get_law_name(abbrev=True)
            )
        if self.street:
            lob["address_line1"] = self.street
        if self.suite:
            lob["address_line2"] = self.suite
        lob["address_city"] = self.city
        lob["address_state"] = self.state
        lob["address_zip"] = self.zip_code
        return lob

    def lob_errors(self, agency):
        """Check that the lob address is well formatted

        Returns a dictionary of all fields over the limit, as well as their
        max length
        """
        limits = {
            "name": 40,
            "company": 40,
            "address_line1": 64,
            "address_line2": 64,
            "city": 200,
        }
        lob_format = self.lob_format(agency)
        errors = {}
        for field, max_len in limits.items():
            if len(lob_format.get(field, "")) > max_len:
                errors[field] = max_len
        return errors

    class Meta:
        verbose_name_plural = "addresses"
        unique_together = (
            "street",
            "suite",
            "city",
            "state",
            "zip_code",
            "agency_override",
            "attn_override",
            "address",
        )


# Communication models


class EmailCommunication(models.Model):
    """An email sent or received to deliver a communication"""

    communication = models.ForeignKey(
        "foia.FOIACommunication", related_name="emails", on_delete=models.CASCADE
    )
    sent_datetime = models.DateTimeField()
    confirmed_datetime = models.DateTimeField(blank=True, null=True)
    from_email = models.ForeignKey(
        EmailAddress,
        blank=True,
        null=True,
        related_name="from_emails",
        on_delete=models.PROTECT,
    )
    to_emails = models.ManyToManyField(EmailAddress, related_name="to_emails")
    cc_emails = models.ManyToManyField(EmailAddress, related_name="cc_emails")

    delivered = "email"

    def __str__(self):
        value = "Email Communication"
        if self.from_email:
            value += ' From: "%s"' % self.from_email
        return value

    def set_raw_email(self, msg):
        """Set the raw email for this communication"""
        # pylint: disable=import-outside-toplevel
        from muckrock.foia.models import RawEmail

        raw_email = RawEmail.objects.get_or_create(email=self)[0]
        raw_email.raw_email = msg
        raw_email.save()

    def sent_to(self):
        """Who was this email sent to?"""
        return self.to_emails.first()

    def sent_from(self):
        """Who was this email sent from?"""
        return self.from_email


class FaxCommunication(models.Model):
    """A fax sent to deliver a communication"""

    communication = models.ForeignKey(
        "foia.FOIACommunication", related_name="faxes", on_delete=models.CASCADE
    )
    sent_datetime = models.DateTimeField()
    confirmed_datetime = models.DateTimeField(blank=True, null=True)
    to_number = models.ForeignKey(
        PhoneNumber,
        blank=True,
        null=True,
        related_name="faxes",
        on_delete=models.PROTECT,
    )
    fax_id = models.CharField(max_length=10, blank=True, default="")

    delivered = "fax"

    def __str__(self):
        return "Fax Communication To %s" % self.to_number

    def sent_to(self):
        """Who was this fax sent to?"""
        return self.to_number

    def sent_from(self):
        """Who was this fax sent from?"""
        return None


class MailCommunication(models.Model):
    """A snail mail sent or received to deliver a communication"""

    communication = models.ForeignKey(
        "foia.FOIACommunication", related_name="mails", on_delete=models.CASCADE
    )
    sent_datetime = models.DateTimeField()
    from_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="from_mails",
    )
    to_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="to_mails",
    )
    pdf = models.FileField(
        upload_to="snail_pdfs/%Y/%m/%d",
        verbose_name="PDF",
        max_length=255,
        blank=True,
        null=True,
    )
    lob_id = models.CharField(max_length=20, blank=True, default="")

    delivered = "mail"

    def __str__(self):
        return "Mail Communication To %s" % self.to_address

    def sent_to(self):
        """Who was this mail sent to?"""
        return self.to_address

    def sent_from(self):
        """Who was this mail sent from?"""
        return self.from_address


class WebCommunication(models.Model):
    """A communication posted to our site directly through our web form"""

    communication = models.ForeignKey(
        "foia.FOIACommunication", related_name="web_comms", on_delete=models.CASCADE
    )
    sent_datetime = models.DateTimeField()

    delivered = "web"

    def __str__(self):
        return "Web Communication"

    def sent_to(self):
        """Who was web comm sent to?"""
        return None

    def sent_from(self):
        """Who was web comm sent from?"""
        return None


class PortalCommunication(models.Model):
    """A communication sent or received from a portal"""

    communication = models.ForeignKey(
        "foia.FOIACommunication", related_name="portals", on_delete=models.CASCADE
    )
    sent_datetime = models.DateTimeField()
    portal = models.ForeignKey(
        "portal.Portal", related_name="communications", on_delete=models.PROTECT
    )
    direction = models.CharField(
        max_length=8, choices=(("incoming", "Incoming"), ("outgoing", "Outgoing"))
    )

    delivered = "portal"

    def __str__(self):
        return "Portal Communication"

    def sent_to(self):
        """Who was portal comm sent to?"""
        if self.direction == "outgoing":
            return self.portal
        else:
            return None

    def sent_from(self):
        """Who was portal comm sent from?"""
        if self.direction == "incoming":
            return self.portal
        else:
            return None


# Error models


class EmailError(models.Model):
    """An error has occured delivering this email"""

    email = models.ForeignKey(
        "communication.EmailCommunication",
        related_name="errors",
        on_delete=models.CASCADE,
    )
    datetime = models.DateTimeField()

    recipient = models.ForeignKey(
        "communication.EmailAddress", related_name="errors", on_delete=models.PROTECT
    )
    code = models.CharField(max_length=10)
    error = models.TextField(blank=True)
    event = models.CharField(max_length=10)
    reason = models.CharField(max_length=255)

    def __str__(self):
        return "Email Error: %s - %s" % (self.email.pk, self.datetime)

    class Meta:
        ordering = ["datetime"]


class FaxError(models.Model):
    """An error has occured delivering this fax"""

    fax = models.ForeignKey(
        "communication.FaxCommunication",
        related_name="errors",
        on_delete=models.CASCADE,
    )
    datetime = models.DateTimeField()

    recipient = models.ForeignKey(
        "communication.PhoneNumber", related_name="errors", on_delete=models.PROTECT
    )
    error_type = models.CharField(blank=True, max_length=255)
    error_code = models.CharField(blank=True, max_length=255)
    error_id = models.PositiveSmallIntegerField(blank=True, null=True)

    def __str__(self):
        return "Fax Error: %s - %s" % (self.fax.pk, self.datetime)

    class Meta:
        ordering = ["datetime"]


# Other models


class EmailOpen(models.Model):
    """An email has been opened"""

    email = models.ForeignKey(
        "communication.EmailCommunication",
        related_name="opens",
        on_delete=models.CASCADE,
    )
    datetime = models.DateTimeField()

    recipient = models.ForeignKey(
        "communication.EmailAddress", related_name="opens", on_delete=models.PROTECT
    )
    city = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    country = models.CharField(max_length=10)

    client_type = models.CharField(max_length=15)
    client_name = models.CharField(max_length=50)
    client_os = models.CharField(max_length=10, verbose_name="Client OS")

    device_type = models.CharField(max_length=10)
    user_agent = models.CharField(max_length=255)
    ip_address = models.CharField(max_length=45, verbose_name="IP Address")

    def __str__(self):
        return "EmailOpen: %s - %s" % (self.email.pk, self.datetime)

    class Meta:
        ordering = ["datetime"]


class MailEvent(models.Model):
    """A letter sent through Lob has had a tracking event occur"""

    mail = models.ForeignKey(
        "communication.MailCommunication",
        related_name="events",
        on_delete=models.CASCADE,
    )
    datetime = models.DateTimeField()
    event = models.CharField(max_length=255)

    def __str__(self):
        return "MailEvent: {} -{} - {}".format(self.mail.pk, self.datetime, self.event)

    class Meta:
        ordering = ["datetime"]


class Check(models.Model):
    """A check we have mailed out, for tracking purposes"""

    number = models.PositiveIntegerField(db_index=True)
    agency = models.ForeignKey(
        "agency.Agency", on_delete=models.PROTECT, related_name="checks"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    communication = models.ForeignKey(
        "foia.FOIACommunication", on_delete=models.CASCADE, related_name="checks"
    )
    user = models.ForeignKey(
        "auth.User", on_delete=models.PROTECT, related_name="checks"
    )
    created_datetime = models.DateTimeField(auto_now_add=True)
    # status date indicates when the check entered its final status.
    # it should be null if and only if the status is pending
    status_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=9, choices=CHECK_STATUS, default="pending")

    class Meta:
        ordering = ["created_datetime"]

    def __str__(self):
        return "Check #{}".format(self.number)

    def send_email(self):
        """Send an email record of this check"""
        foia = self.communication.foia
        if foia.user.is_staff:
            type_ = "Staff"
        else:
            type_ = "User"
        context = {
            "number": self.number,
            "payable_to": self.agency,
            "amount": self.amount,
            "signed_by": self.user.profile.full_name,
            "foia_pk": foia.pk,
            "comm_pk": self.communication.pk,
            "type": type_,
            "today": date.today(),
        }
        body = render_to_string("text/task/check.txt", context)
        msg = EmailMessage(
            subject="[CHECK MAILED] Check #{}".format(self.number),
            body=body,
            to=[settings.CHECK_EMAIL],
            cc=[settings.DEFAULT_FROM_EMAIL],
            bcc=[settings.DIAGNOSTIC_EMAIL],
        )
        msg.send(fail_silently=False)

    def mailed_to(self):
        """Return a formatted address of where this check was mailed to"""
        mails = self.communication.mails.all()
        if mails:
            mail = mails[0]
        else:
            return ""
        return mail.to_address.format(self.agency)

    def mail_events(self):
        """The latest Lob event for this checks mailing"""
        mails = self.communication.mails.all()
        if mails:
            mail = mails[0]
        else:
            return {}

        events = {}
        for event in mail.events.all():
            if "." not in event.event:
                continue
            events[event.event.split(".")[1]] = event.datetime
        if self.status_date:
            events[self.status] = self.status_date
        return events
