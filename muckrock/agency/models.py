"""
Models for the Agency application
"""

from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

from datetime import date
from djgeojson.fields import PointField
from easy_thumbnails.fields import ThumbnailerImageField

from muckrock.jurisdiction.models import Jurisdiction, RequestHelper
from muckrock import fields

STALE_DURATION = 120

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
    status = models.CharField(choices=(
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ), max_length=8, default='pending')
    submitter = models.ForeignKey(User, null=True, blank=True, related_name='+')
    users = models.ManyToManyField(
            'accounts.AgencyUser',
            through='AgencyProfile',
            related_name='agencies')
    # XXX set appeal agency to self if appeal to self?  if null does that mean no appeals?
    appeal_agency = models.ForeignKey('self', null=True, blank=True)
    # XXX delete this
    can_email_appeals = models.BooleanField(default=False)
    payable_to = models.ForeignKey('self', related_name='receivable', null=True, blank=True)
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
    location = PointField(blank=True)
    # XXX delete
    email = models.EmailField(blank=True) # maybe leave email
    other_emails = fields.EmailsListField(blank=True, max_length=255)
    contact_salutation = models.CharField(blank=True, max_length=30)
    contact_first_name = models.CharField(blank=True, max_length=100)
    contact_last_name = models.CharField(blank=True, max_length=100)
    contact_title = models.CharField(blank=True, max_length=255)
    # XXX delete
    url = models.URLField(blank=True, verbose_name='FOIA Web Page', help_text='Begin with http://')
    phone = models.CharField(blank=True, max_length=30)
    # XXX maybe delete fax also?
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
    requires_proxy = models.BooleanField(default=False)

    objects = AgencyQuerySet.as_manager()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('agency-detail', [], {'jurisdiction': self.jurisdiction.slug,
                                      'jidx': self.jurisdiction.pk,
                                      'slug': self.slug, 'idx': self.pk})

    def save(self, *args, **kwargs):
        """Save the agency"""
        self.slug = slugify(self.slug)
        self.name = self.name.strip()
        super(Agency, self).save(*args, **kwargs)

    def get_emails(self, type_='primary'):
        """Returns the email addresses to send to"""
        return [c.get_email() for c in self.get_contacts(type_)
                if c.get_email()]

    def get_primary_emails(self):
        return self.get_emails('primary')

    def link_display(self):
        """Returns link if approved"""
        if self.status == 'approved':
            return mark_safe('<a href="%s">%s</a>' % (self.get_absolute_url(), self.name))
        else:
            return self.name

    def is_stale(self):
        """Should this agency be marked as stale?

        If the latest response to any open request is greater than STALE_DURATION
        days ago, or if no responses to any open request, if the oldest open
        request was sent greater than STALE_DURATION days ago.  If no open requests,
        do not mark as stale."""
        # first find any open requests, if none, not stale
        foias = self.foiarequest_set.get_open().order_by('date_submitted')
        if not foias:
            return False
        # find the latest response to an open request
        latest_responses = []
        for foia in foias:
            response = foia.latest_response()
            if response:
                latest_responses.append(response)
        if latest_responses:
            return min(latest_responses) >= STALE_DURATION
        # no response to open requests, use oldest open request submit date
        return (date.today() - foias[0].date_submitted).days >= STALE_DURATION

    def count_thanks(self):
        """Count how many thanks this agency has received"""
        return (self.foiarequest_set
                .filter(communications__thanks=True)
                .distinct()
                .count())

    def set_primary_contact(self, user):
        """Set a user as the primary contact for this agency"""
        if user.profile.acct_type != 'agency':
            raise ValueError(
                    'User must be an agency user to be the primary contact')

        self.agencyprofile_set.filter(contact_type='primary'
                ).update(contact_type='other')

        agencyprofile, _ = user.agencyprofile_set.get_or_create(agency=self)
        agencyprofile.contact_type = 'primary'
        agencyprofile.save()

    def get_contacts(self, type_):
        """Get all contacts of a given type for this agency"""
        return self.users.filter(agencyprofile__contact_type=type_)

    class Meta:
        # pylint: disable=too-few-public-methods
        verbose_name_plural = 'agencies'


CONTACT_TYPES = (
    ('primary', 'Primary'), # Send to this contact by default
    ('copy', 'Copy'), # CC to this contact by default
    ('appeal', 'Appeal'), # Send to this contact by default for appeals
    ('appeal-copy', 'Appeal Copy'), # CC to this contact by default for appeals
    ('other', 'Other'), # Only send to this contact when they reply to a message
)


class AgencyProfile(models.Model):
    """Many to Many through model"""
    user = models.ForeignKey('accounts.AgencyUser')
    agency = models.ForeignKey('agency.Agency')
    contact_type = models.CharField(
            choices=CONTACT_TYPES,
            max_length=11,
            default='other',
            )
