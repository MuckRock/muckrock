# -*- coding: utf-8 -*-
"""
Models for keeping track of how we send and receive communications
"""

# Django
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.db import models
from django.forms import ValidationError

# Standard Library
from email.utils import getaddresses, parseaddr

# Third Party
from djgeojson.fields import PointField
from localflavor.us.models import USStateField, USZipCodeField
from localflavor.us.us_states import STATE_CHOICES
from phonenumber_field.modelfields import PhoneNumberField

# MuckRock
from muckrock.mailgun.models import WhitelistDomain

PHONE_TYPES = (
    ('fax', 'Fax'),
    ('phone', 'Phone'),
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
        email_address, _ = self.update_or_create(
            email=email,
            defaults={'name': name},
        )
        return email_address

    def fetch_many(self, *addresses, **kwargs):
        """Fetch multiple email address objects based on an email header"""
        name_emails = getaddresses(addresses)
        addresses = []
        for name, email in name_emails:
            try:
                email = self._normalize_email(email)
            except ValidationError:
                if kwargs.get('ignore_errors', True):
                    continue
                else:
                    raise
            email_address, _ = self.update_or_create(
                email=email,
                defaults={'name': name},
            )
            addresses.append(email_address)
        return addresses

    @staticmethod
    def _normalize_email(email):
        """Username is case sensitive, domain is not"""
        validate_email(email)
        username, domain = email.rsplit('@', 1)
        return '%s@%s' % (username, domain.lower())


class EmailAddress(models.Model):
    """An email address"""
    email = models.EmailField(unique=True)
    name = models.CharField(blank=True, max_length=255)
    status = models.CharField(
        max_length=5,
        choices=(('good', 'Good'), ('error', 'Error')),
        default='good',
    )

    objects = EmailAddressQuerySet.as_manager()

    def __unicode__(self):
        if self.name:
            val = u'"%s" <%s>' % (self.name, self.email)
        else:
            val = self.email
        if self.status == 'error':
            val += u' (error)'
        return val

    def get_absolute_url(self):
        """The url for this email address"""
        return reverse('email-detail', kwargs={'idx': self.pk})

    @property
    def domain(self):
        """The domain part of the email address"""
        if '@' not in self.email:
            return ''
        return self.email.rsplit('@', 1)[1]

    def allowed(self, foia=None):
        """Is this email address allowed to post to this FOIA request?"""
        # pylint: disable=too-many-return-statements
        from muckrock.agency.models import AgencyEmail

        allowed_tlds = [
            '.%s.us' % a.lower()
            for (a, _) in STATE_CHOICES
            if a not in ('AS', 'DC', 'GU', 'MP', 'PR', 'VI')
        ]
        allowed_tlds.extend(['.gov', '.mil'])

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
        verbose_name_plural = 'email addresses'


class PhoneNumber(models.Model):
    """A phone number"""
    number = PhoneNumberField(unique=True)
    type = models.CharField(
        max_length=5,
        choices=PHONE_TYPES,
        default='phone',
    )
    status = models.CharField(
        max_length=5,
        choices=(('good', 'Good'), ('error', 'Error')),
        default='good',
    )

    def __unicode__(self):
        if self.status == 'error':
            return u'%s (%s)' % (self.number.as_national, self.status)
        else:
            return self.number.as_national

    def get_absolute_url(self):
        """The url for this phone number"""
        return reverse('phone-detail', kwargs={'idx': self.pk})

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
    point = PointField(blank=True)

    # These are override fields for parts of the address
    agency_override = models.CharField(
        blank=True,
        max_length=255,
        help_text='Override the agency this is addressed to',
    )
    attn_override = models.CharField(
        blank=True,
        max_length=255,
        help_text='Override the attention line to address '
        'this to a particular person',
    )

    # This will become the override field for non-conforming addresses
    address = models.TextField(blank=True)

    def __unicode__(self):
        if self.zip_code:
            address = u'{}, {} {}'.format(
                self.city,
                self.state,
                self.zip_code,
            )
            if self.street and self.suite:
                street = u'{}, {}'.format(self.street, self.suite)
            elif self.street:
                street = self.street
            elif self.attn_override:
                street = self.attn_override
            elif self.agency_override:
                street = self.agency_override
            else:
                return address

            address = u'{}, {}'.format(
                street,
                address,
            )
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
                office = u'Appeal'
            else:
                office = u'Office'
            address.append(
                u'{} {}'.format(
                    agency.jurisdiction.get_law_name(abbrev=True),
                    office,
                )
            )
        if self.suite:
            address.append(self.suite)
        if self.street:
            address.append(self.street)
        address.append(
            u'{}, {} {}'.format(
                self.city,
                self.state,
                self.zip_code,
            )
        )
        return '\n'.join(address)

    class Meta:
        verbose_name_plural = 'addresses'


# Communication models


class EmailCommunication(models.Model):
    """An email sent or received to deliver a communication"""
    communication = models.ForeignKey(
        'foia.FOIACommunication', related_name='emails'
    )
    sent_datetime = models.DateTimeField()
    confirmed_datetime = models.DateTimeField(blank=True, null=True)
    from_email = models.ForeignKey(
        EmailAddress,
        blank=True,
        null=True,
        related_name='from_emails',
    )
    to_emails = models.ManyToManyField(EmailAddress, related_name='to_emails')
    cc_emails = models.ManyToManyField(EmailAddress, related_name='cc_emails')

    delivered = 'email'

    def __unicode__(self):
        value = u'Email Communication'
        if self.from_email:
            value += u' From: "%s"' % self.from_email
        return value

    def set_raw_email(self, msg):
        """Set the raw email for this communication"""
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
        'foia.FOIACommunication', related_name='faxes'
    )
    sent_datetime = models.DateTimeField()
    confirmed_datetime = models.DateTimeField(blank=True, null=True)
    to_number = models.ForeignKey(
        PhoneNumber,
        blank=True,
        null=True,
        related_name='faxes',
    )
    fax_id = models.CharField(max_length=10, blank=True, default='')

    delivered = 'fax'

    def __unicode__(self):
        return u'Fax Communication To %s' % self.to_number

    def sent_to(self):
        """Who was this fax sent to?"""
        return self.to_number

    def sent_from(self):
        """Who was this fax sent from?"""
        return None


class MailCommunication(models.Model):
    """A snail mail sent or received to deliver a communication"""
    communication = models.ForeignKey(
        'foia.FOIACommunication',
        related_name='mails',
    )
    sent_datetime = models.DateTimeField()
    from_address = models.ForeignKey(
        Address,
        blank=True,
        null=True,
        related_name='from_mails',
    )
    to_address = models.ForeignKey(
        Address,
        blank=True,
        null=True,
        related_name='to_mails',
    )
    pdf = models.FileField(
        upload_to='snail_pdfs/%Y/%m/%d',
        verbose_name='PDF',
        max_length=255,
        blank=True,
        null=True,
    )

    delivered = 'mail'

    def __unicode__(self):
        return u'Mail Communication To %s' % self.to_address

    def sent_to(self):
        """Who was this mail sent to?"""
        return self.to_address

    def sent_from(self):
        """Who was this mail sent from?"""
        return self.from_address


class WebCommunication(models.Model):
    """A communication posted to our site directly through our web form"""
    communication = models.ForeignKey(
        'foia.FOIACommunication',
        related_name='web_comms',
    )
    sent_datetime = models.DateTimeField()

    delivered = 'web'

    def __unicode__(self):
        return u'Web Communication'

    def sent_to(self):
        """Who was web comm sent to?"""
        return None

    def sent_from(self):
        """Who was web comm sent from?"""
        return None


class PortalCommunication(models.Model):
    """A communication sent or received from a portal"""
    communication = models.ForeignKey(
        'foia.FOIACommunication',
        related_name='portals',
    )
    sent_datetime = models.DateTimeField()
    portal = models.ForeignKey(
        'portal.Portal',
        related_name='communications',
    )
    direction = models.CharField(
        max_length=8,
        choices=(
            ('incoming', 'Incoming'),
            ('outgoing', 'Outgoing'),
        )
    )

    delivered = 'portal'

    def __unicode__(self):
        return u'Portal Communication'

    def sent_to(self):
        """Who was portal comm sent to?"""
        if self.direction == 'outgoing':
            return self.portal
        else:
            return None

    def sent_from(self):
        """Who was portal comm sent from?"""
        if self.direction == 'incoming':
            return self.portal
        else:
            return None


# Error models


class EmailError(models.Model):
    """An error has occured delivering this email"""
    email = models.ForeignKey(
        'communication.EmailCommunication',
        related_name='errors',
    )
    datetime = models.DateTimeField()

    recipient = models.ForeignKey(
        'communication.EmailAddress',
        related_name='errors',
    )
    code = models.CharField(max_length=10)
    error = models.TextField(blank=True)
    event = models.CharField(max_length=10)
    reason = models.CharField(max_length=255)

    def __unicode__(self):
        return u'Email Error: %s - %s' % (self.email.pk, self.datetime)

    class Meta:
        ordering = ['datetime']


class FaxError(models.Model):
    """An error has occured delivering this fax"""
    fax = models.ForeignKey(
        'communication.FaxCommunication',
        related_name='errors',
    )
    datetime = models.DateTimeField()

    recipient = models.ForeignKey(
        'communication.PhoneNumber',
        related_name='errors',
    )
    error_type = models.CharField(blank=True, max_length=255)
    error_code = models.CharField(blank=True, max_length=255)
    error_id = models.PositiveSmallIntegerField(blank=True, null=True)

    def __unicode__(self):
        return u'Fax Error: %s - %s' % (self.fax.pk, self.datetime)

    class Meta:
        ordering = ['datetime']


# Other models


class EmailOpen(models.Model):
    """An email has been opened"""
    email = models.ForeignKey(
        'communication.EmailCommunication',
        related_name='opens',
    )
    datetime = models.DateTimeField()

    recipient = models.ForeignKey(
        'communication.EmailAddress',
        related_name='opens',
    )
    city = models.CharField(max_length=50)
    region = models.CharField(max_length=50)
    country = models.CharField(max_length=10)

    client_type = models.CharField(max_length=15)
    client_name = models.CharField(max_length=50)
    client_os = models.CharField(max_length=10, verbose_name='Client OS')

    device_type = models.CharField(max_length=10)
    user_agent = models.CharField(max_length=255)
    ip_address = models.CharField(max_length=15, verbose_name='IP Address')

    def __unicode__(self):
        return u'EmailOpen: %s - %s' % (self.email.pk, self.datetime)

    class Meta:
        ordering = ['datetime']
