"""
Models for the Agency application
"""

from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

from datetime import date
from django_hosts.resolvers import reverse as host_reverse
from djgeojson.fields import PointField
from easy_thumbnails.fields import ThumbnailerImageField
import logging

from muckrock.jurisdiction.models import Jurisdiction, RequestHelper
from muckrock import fields
from muckrock.task.models import StaleAgencyTask

logger = logging.getLogger(__name__)

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
    user = models.ForeignKey(User, null=True, blank=True)
    appeal_agency = models.ForeignKey('self', null=True, blank=True)
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
    manual_stale = models.BooleanField(default=False,
        help_text='For marking an agency stale by hand.')
    address = models.TextField(blank=True)
    location = PointField(blank=True)
    email = models.EmailField(blank=True)
    other_emails = fields.EmailsListField(blank=True, max_length=255)
    contact_salutation = models.CharField(blank=True, max_length=30)
    contact_first_name = models.CharField(blank=True, max_length=100)
    contact_last_name = models.CharField(blank=True, max_length=100)
    contact_title = models.CharField(blank=True, max_length=255)
    url = models.URLField(blank=True, verbose_name='FOIA Web Page', help_text='Begin with http://')
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
    requires_proxy = models.BooleanField(default=False)

    objects = AgencyQuerySet.as_manager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
                'agency-detail',
                kwargs={
                    'jurisdiction': self.jurisdiction.slug,
                    'jidx': self.jurisdiction.pk,
                    'slug': self.slug,
                    'idx': self.pk,
                    })

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
            return mark_safe('<a href="%s">%s</a>' % (self.get_absolute_url(), self.name))
        else:
            return self.name

    def is_stale(self):
        """Should this agency be marked as stale?

        If the latest response to any open request is greater than STALE_DURATION
        days ago, or if no responses to any open request, if the oldest open
        request was sent greater than STALE_DURATION days ago.  If no open requests,
        do not mark as stale."""
        # check if agency is manually marked as stale
        if self.manual_stale:
            return True
        # find any open requests, if none, not stale
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

    def mark_stale(self, manual=False):
        """Mark this agency as stale and create a StaleAgencyTask if one doesn't already exist."""
        self.stale = True
        self.manual_stale = manual
        self.save()
        try:
            task, created = StaleAgencyTask.objects.get_or_create(resolved=False, agency=self)
            if created:
                logger.info('Created new StaleAgencyTask <%d> for Agency <%d>', task.pk, self.pk)
        except MultipleObjectsReturned as exception:
            # If there are multiple StaleAgencyTasks returned, just return the first one.
            # We only want this method to return a single task.
            # Also, log the exception as a warning.
            task = StaleAgencyTask.objects.filter(resolved=False, agency=self).first()
            logger.warning(exception)
        return task

    def unmark_stale(self):
        """Unmark this agency as stale and resolve all of its StaleAgencyTasks."""
        self.stale = False
        self.manual_stale = False
        self.save()

    def count_thanks(self):
        """Count how many thanks this agency has received"""
        return (self.foiarequest_set
                .filter(communications__thanks=True)
                .distinct()
                .count())

    def get_requests(self):
        """Just returns the foiareqest_set value. Used for compatability with RequestHeper mixin"""
        return self.foiarequest_set

    class Meta:
        # pylint: disable=too-few-public-methods
        verbose_name_plural = 'agencies'
