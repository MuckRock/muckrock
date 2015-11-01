"""
Models for the Agency application
"""

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify

from datetime import date
from easy_thumbnails.fields import ThumbnailerImageField

from muckrock.jurisdiction.models import Jurisdiction, RequestHelper
from muckrock import fields

class AgencyType(models.Model):
    """Marks an agency as fufilling requests of this type for its jurisdiction"""

    name = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name

    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['name']


class AgencyQuerySet(models.QuerySet):
    """Object manager for Agencies"""
    # pylint: disable=too-many-public-methods

    def get_approved(self):
        """Get all approved agencies"""
        return self.filter(status='approved')

    def get_siblings(self, agency):
        """Get all approved agencies in the same jurisdiction as the given agency."""
        return self.filter(jurisdiction=agency.jurisdiction)\
                   .exclude(id=agency.id)\
                   .filter(status='approved')\
                   .order_by('name')


class Agency(models.Model, RequestHelper):
    """An agency for a particular jurisdiction that has at least one agency type"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    jurisdiction = models.ForeignKey(Jurisdiction, related_name='agencies')
    types = models.ManyToManyField(AgencyType, blank=True)
    approved = models.BooleanField(default=False)
    status = models.CharField(choices=(
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ), max_length=8, default='pending')
    user = models.ForeignKey(User, null=True, blank=True)
    appeal_agency = models.ForeignKey('self', null=True, blank=True)
    can_email_appeals = models.BooleanField(default=False)
    image = ThumbnailerImageField(
        upload_to='agency_images',
        blank=True,
        null=True,
        resize_source={'size': (900, 600), 'crop': 'smart'}
    )
    image_attr_line = models.CharField(blank=True, max_length=255, help_text='May use html')
    public_notes = models.TextField(blank=True, help_text='May use html')
    stale = models.BooleanField(default=False)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    other_emails = fields.EmailsListField(blank=True, max_length=255)
    contact_salutation = models.CharField(blank=True, max_length=30)
    contact_first_name = models.CharField(blank=True, max_length=100)
    contact_last_name = models.CharField(blank=True, max_length=100)
    contact_title = models.CharField(blank=True, max_length=255)
    url = models.URLField(blank=True, verbose_name='FOIA Web Page', help_text='Begin with http://')
    expires = models.DateField(blank=True, null=True)
    phone = models.CharField(blank=True, max_length=30)
    fax = models.CharField(blank=True, max_length=30)
    notes = models.TextField(blank=True)
    aliases = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    website = models.CharField(max_length=255, blank=True)
    twitter = models.CharField(max_length=255, blank=True)
    twitter_handles = models.TextField(blank=True)
    foia_logs = models.URLField(blank=True, verbose_name='FOIA Logs',
                                help_text='Begin with http://')
    foia_guide = models.URLField(blank=True, verbose_name='FOIA Processing Guide',
                                 help_text='Begin with http://')
    exempt = models.BooleanField(default=False)

    objects = AgencyQuerySet.as_manager()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        # pylint: disable=no-member
        return ('agency-detail', [], {'jurisdiction': self.jurisdiction.slug,
                                      'jidx': self.jurisdiction.pk,
                                      'slug': self.slug, 'idx': self.pk})

    def save(self, *args, **kwargs):
        """Save the agency"""
        self.email = self.email.strip()
        self.slug = slugify(self.slug)
        self.name = self.name.strip()
        super(Agency, self).save(*args, **kwargs)

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

    def link_display(self):
        """Returns link if approved"""
        if self.status == 'approved':
            return '<a href="%s">%s</a>' % (self.get_absolute_url(), self.name)
        else:
            return self.name

    def expired(self):
        """Is this agency expired?"""

        if self.expires:
            return self.expires < date.today()

    def latest_response(self):
        """When was the last time we heard from them?"""
        # pylint: disable=no-member
        foias = self.foiarequest_set.get_open()
        latest_responses = []
        for foia in foias:
            response = foia.latest_response()
            if response:
                latest_responses.append(response)
        if latest_responses:
            return max(latest_responses)

    class Meta:
        # pylint: disable=too-few-public-methods
        verbose_name_plural = 'agencies'

