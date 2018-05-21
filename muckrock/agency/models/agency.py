"""
Agency Model
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

# Standard Library
import logging
from datetime import date

# Third Party
from djgeojson.fields import PointField
from easy_thumbnails.fields import ThumbnailerImageField

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.accounts.utils import unique_username
from muckrock.jurisdiction.models import Jurisdiction, RequestHelper
from muckrock.task.models import NewAgencyTask

logger = logging.getLogger(__name__)


class AgencyType(models.Model):
    """Marks an agency as fufilling requests of this type for its jurisdiction"""

    name = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class AgencyQuerySet(models.QuerySet):
    """Object manager for Agencies"""

    # pylint: disable=too-many-public-methods

    def get_approved(self):
        """Get all approved agencies"""
        return self.filter(status='approved')

    def get_approved_and_pending(self, user):
        """Get approved and given user's pending agencies"""
        if user.is_authenticated:
            return self.filter(
                Q(status='approved') | Q(status='pending', user=user)
            )
        else:
            return self.get_approved()

    def get_siblings(self, agency):
        """Get all approved agencies in the same jurisdiction as the given agency."""
        return self.filter(jurisdiction=agency.jurisdiction)\
                   .exclude(id=agency.id)\
                   .filter(status='approved')\
                   .order_by('name')

    def create_new(self, name, jurisdiction_pk, user):
        """Create a pending agency with a NewAgency task"""
        user = user if user.is_authenticated else None
        name = name.strip()

        existing_agency = self.filter(
            name=name,
            jurisdiction_id=jurisdiction_pk,
            user=user,
            status='pending',
        ).first()
        if existing_agency:
            return existing_agency

        agency = self.create(
            name=name,
            slug=(slugify(name) or 'untitled'),
            jurisdiction_id=jurisdiction_pk,
            user=user,
            status='pending',
        )
        NewAgencyTask.objects.create(
            user=user,
            agency=agency,
        )
        return agency


class Agency(models.Model, RequestHelper):
    """An agency for a particular jurisdiction that has at least one agency type"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    jurisdiction = models.ForeignKey(Jurisdiction, related_name='agencies')
    types = models.ManyToManyField(AgencyType, blank=True)
    status = models.CharField(
        choices=(
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        max_length=8,
        default='pending'
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        help_text='The user who submitted this agency',
    )
    appeal_agency = models.ForeignKey('self', null=True, blank=True)
    payable_to = models.ForeignKey(
        'self', related_name='receivable', null=True, blank=True
    )
    image = ThumbnailerImageField(
        upload_to='agency_images',
        blank=True,
        null=True,
        resize_source={
            'size': (900, 600),
            'crop': 'smart'
        }
    )
    image_attr_line = models.CharField(
        blank=True, max_length=255, help_text='May use html'
    )
    public_notes = models.TextField(blank=True, help_text='May use html')
    location = PointField(blank=True)

    addresses = models.ManyToManyField(
        'communication.Address',
        through='AgencyAddress',
        related_name='agencies',
    )
    emails = models.ManyToManyField(
        'communication.EmailAddress',
        through='AgencyEmail',
        related_name='agencies',
    )
    phones = models.ManyToManyField(
        'communication.PhoneNumber',
        through='AgencyPhone',
        related_name='agencies',
    )
    portal = models.ForeignKey(
        'portal.Portal',
        related_name='agencies',
        blank=True,
        null=True,
    )
    contact_salutation = models.CharField(blank=True, max_length=30)
    contact_first_name = models.CharField(blank=True, max_length=100)
    contact_last_name = models.CharField(blank=True, max_length=100)
    contact_title = models.CharField(blank=True, max_length=255)

    form = models.ForeignKey(
        'AgencyRequestForm',
        blank=True,
        null=True,
        related_name='agencies',
        on_delete=models.SET_NULL,
    )

    url = models.URLField(
        blank=True,
        verbose_name='FOIA Web Page',
        help_text='Begin with http://'
    )
    notes = models.TextField(blank=True)
    aliases = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children'
    )

    website = models.CharField(max_length=255, blank=True)
    twitter = models.CharField(max_length=255, blank=True)
    twitter_handles = models.TextField(blank=True)
    foia_logs = models.URLField(
        blank=True, verbose_name='FOIA Logs', help_text='Begin with http://'
    )
    foia_guide = models.URLField(
        blank=True,
        verbose_name='FOIA Processing Guide',
        help_text='Begin with http://'
    )
    exempt = models.BooleanField(default=False)
    exempt_note = models.CharField(max_length=255, blank=True)
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
            }
        )

    def save(self, *args, **kwargs):
        """Save the agency"""
        self.slug = slugify(self.slug)
        self.name = self.name.strip()
        super(Agency, self).save(*args, **kwargs)

    def link_display(self):
        """Returns link if approved"""
        if self.status == 'approved':
            return mark_safe(
                '<a href="%s">%s</a>' % (self.get_absolute_url(), self.name)
            )
        else:
            return self.name

    def count_thanks(self):
        """Count how many thanks this agency has received"""
        return (
            self.foiarequest_set.filter(communications__thanks=True)
            .distinct().count()
        )

    def get_requests(self):
        """Just returns the foiareqest_set value. Used for compatability with RequestHeper mixin"""
        return self.foiarequest_set

    def get_user(self):
        """Get the agency user for this agency"""
        try:
            return self.profile.user
        except Profile.DoesNotExist:
            user = User.objects.create_user(unique_username(self.name))
            Profile.objects.create(
                user=user,
                acct_type='agency',
                date_update=date.today(),
                agency=self,
            )
            return user

    def get_emails(self, request_type='primary', email_type='to'):
        """Get the specified type of email addresses for this agency"""
        return self.emails.filter(
            status='good',
            agencyemail__request_type=request_type,
            agencyemail__email_type=email_type,
        )

    def get_faxes(self, request_type='primary'):
        """Get the contact fax numbers"""
        return self.phones.filter(
            type='fax',
            status='good',
            agencyphone__request_type=request_type,
        )

    def get_phones(self, request_type='none'):
        """Get the phone numbers"""
        return self.phones.filter(
            type='phone',
            agencyphone__request_type=request_type,
        )

    def get_addresses(self, request_type='primary'):
        """Get the contact addresses"""
        return self.addresses.filter(agencyaddress__request_type=request_type,)

    def get_proxy_info(self):
        """Handle proxy users for request creation in this agency"""
        if self.requires_proxy:
            proxy_user = self.jurisdiction.get_proxy()
            if proxy_user is None:
                return {
                    'from_user': User.objects.get(username='Proxy'),
                    'proxy': True,
                    'missing_proxy': True,
                    'warning':
                        'This agency and jurisdiction requires requestors to be '
                        'in-state citizens.  We do not currently have a citizen proxy '
                        'requestor on file for this state, but will attempt to find '
                        'one to submit this request on your behalf.',
                }
            else:
                return {
                    'from_user': proxy_user,
                    'proxy': True,
                    'missing_proxy': False,
                    'warning':
                        'This agency and jurisdiction requires requestors to be '
                        'in-state citizens.  This request will be filed in the name '
                        'of one of our volunteer filers for this state.',
                }
        else:
            return {'proxy': False, 'missing_proxy': False}

    def has_open_review_task(self):
        """Is there an open review agency task for this agency"""
        return self.reviewagencytask_set.filter(resolved=False).exists()

    @property
    def email(self):
        """The main email"""
        return self.get_emails('primary', 'to').first()

    @property
    def other_emails(self):
        """The cc emails"""
        return self.get_emails('primary', 'cc')

    @property
    def fax(self):
        """The primary fax"""
        return self.get_faxes('primary').first()

    @property
    def address(self):
        """The primary address"""
        return self.get_addresses('primary').first()

    class Meta:
        verbose_name_plural = 'agencies'
        permissions = (('view_emails', 'Can view private contact information'),)
