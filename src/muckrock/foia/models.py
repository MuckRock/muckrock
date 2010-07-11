"""
Models for the FOIA application
"""

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.template.loader import render_to_string

from datetime import datetime, date, timedelta
import os

from muckrock.utils import try_or_none

class FOIARequestManager(models.Manager):
    """Object manager for FOIA requests"""
    # pylint: disable-msg=R0904

    def get_submitted(self):
        """Get all submitted FOIA requests"""
        return self.filter(status__in=['submitted', 'processed', 'fix', 'rejected', 'done'])

    def get_done(self):
        """Get all FOIA requests with responses"""
        return self.filter(status='done')

    def get_editable(self):
        """Get all editable FOIA requests"""
        return self.filter(status__in=['started', 'fix'])

    def get_viewable(self, user):
        """Get all viewable FOIA requests for given user"""
        # Requests are visible if you own them, or if they are not drafts and not embargoed
        if user.is_authenticated():
            return self.filter(Q(user=user) |
                               (~Q(status='started') &
                                ~Q(embargo=True, date_done__gt=datetime.today() - timedelta(30))))
        else:
            # anonymous user, filter out drafts and embargoes
            return self.exclude(status='started')\
                       .exclude(embargo=True, date_done__gt=datetime.today() - timedelta(30))


class FOIARequest(models.Model):
    """A Freedom of Information Act request"""

    status = (
        ('started', 'Started'),
        ('submitted', 'Submitted'),
        ('processed', 'Processed'),
        ('fix', 'Fix required'),
        ('rejected', 'Rejected'),
        ('done', 'Response received'),
    )

    user = models.ForeignKey(User)
    title = models.CharField(max_length=70)
    slug = models.SlugField(max_length=70)
    status = models.CharField(max_length=10, choices=status)
    jurisdiction = models.ForeignKey('Jurisdiction', null=True)
    agency_type = models.ForeignKey('AgencyType', null=True)
    request = models.TextField()
    response = models.TextField(blank=True)
    date_submitted = models.DateField(blank=True, null=True)
    date_done = models.DateField(blank=True, null=True, verbose_name='Date response received')
    date_due = models.DateField(blank=True, null=True)
    embargo = models.BooleanField()

    objects = FOIARequestManager()

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        # pylint: disable-msg=E1101
        return ('foia-detail', [], {'jurisdiction': self.jurisdiction.slug,
                                    'slug': self.slug, 'idx': self.id})

    def is_editable(self):
        """Can this request be updated?"""
        return self.status == 'started' or self.status == 'fix'

    def is_deletable(self):
        """Can this request be deleted?"""
        return self.status == 'started'

    def is_viewable(self, user):
        """Is this request viewable?"""
        return self.user == user or (self.status != 'started' and not self.is_embargo())

    def is_embargo(self, user=None):
        """Is this request currently on an embargo?"""
        if user and user == self.user:
            # Don't embargo from yourself
            return False
        else:
            return self.embargo and self.date_done and \
                    (date.today() - self.date_done) < timedelta(30)

    def doc_first_page(self):
        """Get the first page of this requests corresponding document"""
        # pylint: disable-msg=E1101
        return self.images.get(page=1)

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['title']
        verbose_name = 'FOIA Request'


class FOIAImage(models.Model):
    """An image attached to a FOIA request"""
    # pylint: disable-msg=E1101
    foia = models.ForeignKey(FOIARequest, related_name='images')
    image = models.ImageField(upload_to='foia_images')
    page = models.SmallIntegerField()

    def __unicode__(self):
        return '%s Document Page %d' % (self.foia.title, self.page)

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('foia-doc-detail', [],
                {'jurisdiction': self.foia.jurisdiction.slug,
                 'slug': self.foia.slug,
                 'idx': self.foia.id,
                 'page': self.page})

    def next(self):
        """Get next document page"""
        return try_or_none(self.DoesNotExist, self.foia.images.get, page=self.page + 1)

    def previous(self):
        """Get previous document page"""
        return try_or_none(self.DoesNotExist, self.foia.images.get, page=self.page - 1)

    def total_pages(self):
        """Get total page count"""
        return self.foia.images.count()

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['page']
        verbose_name = 'FOIA Document Image'
        unique_together = (('foia', 'page'),)


class FOIAFile(models.Model):
    """An arbitrary file attached to a FOIA request"""
    # pylint: disable-msg=E1101
    foia = models.ForeignKey(FOIARequest, related_name='files')
    ffile = models.FileField(upload_to='foia_files')

    def __unicode__(self):
        return 'File: %s' % self.ffile.name

    def name(self):
        """Return the basename of the file"""
        return os.path.basename(self.ffile.name)

    class Meta:
        # pylint: disable-msg=R0903
        verbose_name = 'FOIA Document File'


class Jurisdiction(models.Model):
    """A jursidiction that you may file FOIA requests in"""

    levels = ( ('n', 'National'), ('s', 'State'), ('l', 'Local') )

    name = models.CharField(max_length=50)
    # slug should be slugify(unicode(self))
    slug = models.SlugField(max_length=55)
    abbrev = models.CharField(max_length=5, blank=True)
    level = models.CharField(max_length=1, choices=levels)
    parent = models.ForeignKey('self', related_name='children', blank=True, null=True)

    def __unicode__(self):
        # pylint: disable-msg=E1101
        if self.level == 'l':
            return '%s, %s' % (self.name, self.parent.abbrev)
        else:
            return self.name

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['name']


class AgencyType(models.Model):
    """Marks an agency as fufilling requests of this type for its jurisdiction"""

    name = models.CharField(max_length=60)

    def __unicode__(self):
        return self.name

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['name']


class Agency(models.Model):
    """An agency for a particular jurisdiction that has at least one agency type"""

    name = models.CharField(max_length=60)
    jurisdiction = models.ForeignKey(Jurisdiction, related_name='agencies')
    types = models.ManyToManyField(AgencyType)
    address = models.TextField()
    email = models.EmailField(blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        # pylint: disable-msg=R0903
        verbose_name_plural = 'agencies'


def foia_save_handler(sender, **kwargs):
    """Log changes to FOIA Requests"""
    # pylint: disable-msg=W0613

    request = kwargs['instance']
    try:
        old_request = FOIARequest.objects.get(pk=request.pk)
    except FOIARequest.DoesNotExist:
        # if we are saving a new FOIA Request, do not email them
        return

    if request.status != old_request.status and \
            request.status in ['processed', 'fix', 'rejected', 'done']:
        msg = render_to_string('foia/mail.txt',
            {'name': request.user.get_full_name(),
             'title': request.title,
             'status': request.get_status_display(),
             'link': request.get_absolute_url()})
        send_mail('[MuckRock] FOIA request has been updated',
                  msg, 'info@muckrock.com', [request.user.email], fail_silently=False)

pre_save.connect(foia_save_handler, sender=FOIARequest, dispatch_uid='muckrock.foia.models')
