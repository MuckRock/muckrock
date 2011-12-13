"""
Models for the Agency application
"""

from django.contrib.auth.models import User
from django.db import models

from jurisdiction.models import Jurisdiction, RequestHelper
import fields

class AgencyType(models.Model):
    """Marks an agency as fufilling requests of this type for its jurisdiction"""

    name = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name

    class Meta:
        # pylint: disable=R0903
        ordering = ['name']


class Agency(models.Model, RequestHelper):
    """An agency for a particular jurisdiction that has at least one agency type"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    jurisdiction = models.ForeignKey(Jurisdiction, related_name='agencies')
    types = models.ManyToManyField(AgencyType, blank=True)
    approved = models.BooleanField()
    user = models.ForeignKey(User, null=True, blank=True)
    appeal_agency = models.ForeignKey('self', null=True, blank=True)
    can_email_appeals = models.BooleanField()

    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    other_emails = fields.EmailsListField(blank=True, max_length=255)
    contact_salutation = models.CharField(blank=True, max_length=30)
    contact_first_name = models.CharField(blank=True, max_length=100)
    contact_last_name = models.CharField(blank=True, max_length=100)
    contact_title = models.CharField(blank=True, max_length=255)
    url = models.URLField(blank=True, verbose_name='Website', help_text='Begin with http://')
    expires = models.DateField(blank=True, null=True)
    phone = models.CharField(blank=True, max_length=20)
    fax = models.CharField(blank=True, max_length=20)
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        # pylint: disable=E1101
        return ('agency-detail', [], {'jurisdiction': self.jurisdiction.slug,
                                      'slug': self.slug, 'idx': self.pk})

    def normalize_fax(self):
        """Return a fax number suitable for use in a faxaway email address"""

        fax = ''.join(c for c in self.fax if c.isdigit())
        if len(fax) == 10:
            return '1' + fax
        if len(fax) == 11 and fax[0] == '1':
            return fax
        return None

    def get_email(self):
        """Returns an email address to send to"""

        if self.email:
            return self.email
        elif self.normalize_fax():
            return '%s@fax2.faxaway.com' % self.normalize_fax()
        else:
            return ''

    def get_other_emails(self):
        """Returns other emails as a list"""
        return fields.email_separator_re.split(self.other_emails)

    class Meta:
        # pylint: disable=R0903
        verbose_name_plural = 'agencies'

