"""
Models for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.template.loader import render_to_string

from datetime import datetime, date, timedelta
import os
import re

from muckrock.models import ChainableManager

class FOIARequestManager(ChainableManager):
    """Object manager for FOIA requests"""
    # pylint: disable-msg=R0904

    def get_submitted(self):
        """Get all submitted FOIA requests"""
        return self.exclude(status='started')

    def get_done(self):
        """Get all FOIA requests with responses"""
        return self.filter(status='done')

    def get_editable(self):
        """Get all editable FOIA requests"""
        return self.filter(Q(status__in=['started', 'fix']) | Q(tracker=True))

    def get_viewable(self, user):
        """Get all viewable FOIA requests for given user"""
        # Requests are visible if you own them, or if they are not drafts and not embargoed
        # and not tracker only
        if user.is_authenticated():
            return self.filter(Q(user=user) |
                               (~Q(status='started') &
                                ~Q(embargo=True, date_done__gt=datetime.today() - timedelta(30)) &
                                ~Q(embargo=True, date_done=None) &
                                ~Q(tracker=True)))
        else:
            # anonymous user, filter out drafts and embargoes and tracker only
            return self.exclude(status='started') \
                       .exclude(embargo=True, date_done__gt=datetime.today() - timedelta(30)) \
                       .exclude(embargo=True, date_done=None) \
                       .exclude(tracker=True)

    def get_public(self):
        """Get all publically viewable FOIA requests"""
        return self.get_viewable(AnonymousUser())

    def get_overdue(self):
        """Get all overdue FOIA requests"""
        return self.filter(status='processed', date_due__lt=date.today())


class FOIARequest(models.Model):
    """A Freedom of Information Act request"""

    status = (
        ('started', 'Draft'),
        ('submitted', 'Processing'),
        ('processed', 'Awaiting Response'),
        ('fix', 'Fix Required'),
        ('payment', 'Payment Required'),
        ('rejected', 'Rejected'),
        ('done', 'Completed'),
        ('partial', 'Partially Completed'),
    )

    user = models.ForeignKey(User)
    title = models.CharField(max_length=70)
    slug = models.SlugField(max_length=70)
    status = models.CharField(max_length=10, choices=status)
    jurisdiction = models.ForeignKey('Jurisdiction')
    agency = models.ForeignKey('Agency', blank=True, null=True)
    date_submitted = models.DateField(blank=True, null=True)
    date_done = models.DateField(blank=True, null=True, verbose_name='Date response received')
    date_due = models.DateField(blank=True, null=True)
    embargo = models.BooleanField()
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    description = models.TextField(blank=True)
    featured = models.BooleanField()
    tracker = models.BooleanField()

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
        return self.status == 'started' or self.status == 'fix' or self.tracker

    def is_deletable(self):
        """Can this request be deleted?"""
        return self.status == 'started' or self.tracker

    def is_viewable(self, user):
        """Is this request viewable?"""
        return self.user == user or (self.status != 'started' and not self.is_embargo()
                                     and not self.tracker)

    def is_embargo(self):
        """Is this request currently on an embargo?"""
        if not self.embargo:
            return False
        elif not self.date_done:
            return True
        else:
            return date.today() < self.embargo_date()

    def embargo_date(self):
        """The date this request comes off of embargo"""
        if self.embargo and self.date_done:
            return self.date_done + timedelta(30)

    def public_documents(self):
        """Get a list of public documents attached to this request"""
        # pylint: disable-msg=E1101
        return self.documents.filter(access='public').exclude(doc_id='')

    def percent_complete(self):
        """Get percent complete for the progress bar"""
        percents = {'started': 25, 'submitted': 50, 'processed': 75,
                    'fix':     75, 'payment':   75, 'rejected': 100,
                    'done':   100, 'partial':   90}
        return percents[self.status]

    def color_code(self):
        """Get the color code for the current status"""
        processed = 'stop' if self.date_due and date.today() > self.date_due else 'go'
        colors = {'started': 'wait', 'submitted': 'go',   'processed': processed,
                  'fix':     'wait', 'payment':   'wait', 'rejected':  'stop',
                  'done':      'go', 'partial': 'go'}
        return colors[self.status]

    def first_request(self):
        """Return the first request text"""
        # pylint: disable-msg=E1101
        return self.communications.all()[0].communication

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['title']
        verbose_name = 'FOIA Request'


class FOIACommunication(models.Model):
    """A single communication of a FOIA request"""

    foia = models.ForeignKey(FOIARequest, related_name='communications')
    from_who = models.CharField(max_length=70)
    date = models.DateField()
    response = models.BooleanField(help_text='Is this a response (or a request)?')
    full_html = models.BooleanField()
    communication = models.TextField()

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['foia', 'date']
        verbose_name = 'FOIA Communication'


class FOIADocument(models.Model):
    """A DocumentCloud document attached to a FOIA request"""

    access = (('public', 'Public'), ('private', 'Private'), ('organization', 'Organization'))

    # pylint: disable-msg=E1101
    foia = models.ForeignKey(FOIARequest, related_name='documents')
    document = models.FileField(upload_to='foia_documents')
    title = models.CharField(max_length=70)
    source = models.CharField(max_length=70)
    description = models.TextField()
    access = models.CharField(max_length=12, choices=access)
    doc_id = models.SlugField(max_length=80, editable=False)
    pages = models.PositiveIntegerField(default=0, editable=False)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """The url for this object"""
        return '%s#%s' % (self.foia.get_absolute_url(), self.doc_id)

    def get_thumbnail(self):
        """Get the url to the thumbnail image"""
        match = re.match('^(\d+)-(.*)$', self.doc_id)
        if not match:
            return None
        else:
            return 'http://s3.documentcloud.org/documents/'\
                   '%s/pages/%s-p1-thumbnail.gif' % match.groups()

    def is_viewable(self, user):
        """Is this document viewable to user"""
        return self.access == 'public' and self.foia.is_viewable(user)

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.is_viewable(AnonymousUser())

    class Meta:
        # pylint: disable-msg=R0903
        verbose_name = 'FOIA DocumentCloud Document'


class FOIADocTopViewed(models.Model):
    """Keep track of the top 5 most viewed documents for the front page"""

    doc = models.ForeignKey(FOIADocument)
    rank = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['rank']
        verbose_name = 'FOIA Top Viewed Document'


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

    levels = ( ('f', 'Federal'), ('s', 'State'), ('l', 'Local') )

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

    def legal(self):
        """Return the jurisdiction abbreviation for which law this jurisdiction falls under"""
        # pylint: disable-msg=E1101
        if self.level == 'l':
            return self.parent.abbrev
        else:
            return self.abbrev

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
    types = models.ManyToManyField(AgencyType, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    approved = models.BooleanField()

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
            request.status in ['processed', 'fix', 'payment', 'rejected', 'done', 'partial']:
        msg = render_to_string('foia/mail.txt',
            {'name': request.user.get_full_name(),
             'title': request.title,
             'status': request.get_status_display(),
             'link': request.get_absolute_url()})
        send_mail('[MuckRock] FOIA request has been updated',
                  msg, 'info@muckrock.com', [request.user.email], fail_silently=False)
    if request.status == 'submitted':
        send_mail('[MuckRock] FOIA request has been submitted',
                  'http://www.muckrock.com' + request.get_absolute_url(),
                  'info@muckrock.com', ['morisy@gmail.com'], fail_silently=False)

pre_save.connect(foia_save_handler, sender=FOIARequest, dispatch_uid='muckrock.foia.models')
