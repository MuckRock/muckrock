"""
M2M Through Models for Agency communication addresses
"""

# Django
from django.db import models

REQUEST_TYPES = (
    ('primary', 'Primary'),
    ('appeal', 'Appeal'),
    ('none', 'None'),
)

EMAIL_TYPES = (
    ('to', 'To'),
    ('cc', 'CC'),
    ('none', 'None'),
)

# pylint: disable=model-missing-unicode


class AgencyAddress(models.Model):
    """Through model for agency to address M2M"""

    agency = models.ForeignKey('Agency')
    address = models.ForeignKey('communication.Address')
    request_type = models.CharField(
        max_length=7,
        choices=REQUEST_TYPES,
        default='none',
    )

    def __unicode__(self):
        val = unicode(self.address)
        if self.request_type != 'none':
            val = '%s\n(%s)' % (val, self.request_type)
        return val


class AgencyEmail(models.Model):
    """Through model for agency to email M2M"""

    agency = models.ForeignKey('Agency')
    email = models.ForeignKey('communication.EmailAddress')
    request_type = models.CharField(
        max_length=7,
        choices=REQUEST_TYPES,
        default='none',
    )
    email_type = models.CharField(
        max_length=4,
        choices=EMAIL_TYPES,
        default='none',
    )

    def __unicode__(self):
        val = unicode(self.email)
        if self.request_type != 'none' and self.email_type != 'none':
            val = '%s (%s - %s)' % (val, self.request_type, self.email_type)
        return val


class AgencyPhone(models.Model):
    "," "Through model for agency to phone M2M" ""

    agency = models.ForeignKey('Agency')
    phone = models.ForeignKey('communication.PhoneNumber')
    request_type = models.CharField(
        max_length=7,
        choices=REQUEST_TYPES,
        default='none',
    )

    def __unicode__(self):
        val = unicode(self.phone)
        if self.request_type != 'none':
            val = '%s (%s)' % (val, self.request_type)
        return val
