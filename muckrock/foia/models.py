"""
Models for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.core.mail import send_mail, send_mass_mail, EmailMessage
from django.core.urlresolvers import reverse
from django.db import models, connection, transaction
from django.db.models import Q, Sum
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import Context

from datetime import datetime, date, timedelta
from hashlib import md5
from itertools import chain
from taggit.managers import TaggableManager
from urlauth.models import AuthKey
import dbsettings
import logging
import os
import re

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.models import ChainableManager
from muckrock.settings import MAILGUN_SERVER_NAME, STATIC_URL
from muckrock.tags.models import Tag, TaggedItemBase
from muckrock.values import TextValue
from muckrock import fields

logger = logging.getLogger(__name__)

class EmailOptions(dbsettings.Group):
    """DB settings for sending email"""
    email_footer = TextValue('email footer')
options = EmailOptions()


class FOIARequestManager(ChainableManager):
    """Object manager for FOIA requests"""
    # pylint: disable=R0904

    def get_submitted(self):
        """Get all submitted FOIA requests"""
        return self.exclude(status='started')

    def get_done(self):
        """Get all FOIA requests with responses"""
        return self.filter(status='done').exclude(date_done=None)

    def get_editable(self):
        """Get all editable FOIA requests"""
        return self.filter(status='started')

    def get_viewable(self, user):
        """Get all viewable FOIA requests for given user"""

        if user.is_staff:
            return self.all()

        # Requests are visible if you own them, or if they are not drafts and not embargoed
        if user.is_authenticated():
            return self.filter(Q(user=user) |
                               (~Q(status='started') &
                                ~Q(embargo=True, date_embargo=None) &
                                ~Q(embargo=True, date_embargo__gt=date.today())))
        else:
            # anonymous user, filter out drafts and embargoes
            return self.exclude(status='started') \
                       .exclude(embargo=True, date_embargo=None) \
                       .exclude(embargo=True, date_embargo__gt=date.today())

    def get_public(self):
        """Get all publically viewable FOIA requests"""
        return self.get_viewable(AnonymousUser())

    def get_overdue(self):
        """Get all overdue FOIA requests"""
        return self.filter(status='processed', date_due__lt=date.today())

    def get_followup(self):
        """Get requests which require us to follow up on with the agency"""

        return [f for f in self.get_overdue()
                  if f.communications.all().reverse()[0].date + timedelta(15) < datetime.now()]
        # Change to this after all follow ups have been resolved
        #return self.filter(status='processed', date_followup__lte=date.today())

    def get_open(self):
        """Get requests which we are awaiting a response from"""
        return self.filter(status__in=['processed', 'appealing'])

    def get_undated(self):
        """Get requests which have an undated file"""
        return self.filter(~Q(files=None) & Q(files__date=None)).distinct()


STATUS = (
    ('started', 'Draft'),
    ('submitted', 'Processing'),
    ('processed', 'Awaiting Response'),
    ('appealing', 'Awaiting Appeal'),
    ('fix', 'Fix Required'),
    ('payment', 'Payment Required'),
    ('rejected', 'Rejected'),
    ('no_docs', 'No Responsive Documents'),
    ('done', 'Completed'),
    ('partial', 'Partially Completed'),
    ('abandoned', 'Withdrawn'),
)

class FOIARequest(models.Model):
    """A Freedom of Information Act request"""
    # pylint: disable=R0904
    # pylint: disable=R0902

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS)
    jurisdiction = models.ForeignKey(Jurisdiction)
    agency = models.ForeignKey(Agency, blank=True, null=True)
    date_submitted = models.DateField(blank=True, null=True)
    date_done = models.DateField(blank=True, null=True, verbose_name='Date response received')
    date_due = models.DateField(blank=True, null=True)
    days_until_due = models.IntegerField(blank=True, null=True)
    date_followup = models.DateField(blank=True, null=True)
    embargo = models.BooleanField()
    date_embargo = models.DateField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    requested_docs = models.TextField(blank=True)
    description = models.TextField(blank=True)
    featured = models.BooleanField()
    tracker = models.BooleanField()
    sidebar_html = models.TextField(blank=True)
    tracking_id = models.CharField(blank=True, max_length=255)
    mail_id = models.CharField(blank=True, max_length=255, editable=False)
    updated = models.BooleanField()
    email = models.EmailField(blank=True)
    other_emails = fields.EmailsListField(blank=True, max_length=255)
    times_viewed = models.IntegerField(default=0)

    objects = FOIARequestManager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    foia_type = 'foia'

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        # pylint: disable=E1101
        return ('foia-detail', [], {'jurisdiction': self.jurisdiction.slug,
                                    'jidx': self.jurisdiction.pk,
                                    'slug': self.slug, 'idx': self.pk})

    def is_editable(self):
        """Can this request be updated?"""
        return self.status == 'started'

    def is_fixable(self):
        """Can this request be ammended by the user?"""
        return self.status == 'fix'

    def is_appealable(self):
        """Can this request be appealed by the user?"""
        if self.status in ['processed', 'appealing']:
            # can appeal these only if they are over due
            if not self.date_due:
                return False
            return self.date_due < date.today()

        # otherwise it can be appealed as long as it has actually been sent to the agency
        return self.status not in ['started', 'submitted']

    def is_payable(self):
        """Can this request be payed for by the user?"""
        return self.status == 'payment' and self.price > 0 and not self.has_crowdfund()

    def is_deletable(self):
        """Can this request be deleted?"""
        return self.status == 'started'

    def is_viewable(self, user):
        """Is this request viewable?"""
        return user.is_staff or self.user == user or \
            (self.status != 'started' and not self.is_embargo())

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.is_viewable(AnonymousUser())

    def is_embargo(self, save=True):
        """Is this request currently on an embargo?"""
        if not self.embargo:
            return False

        if not self.embargo_date() or date.today() < self.embargo_date():
            return True

        if save:
            logger.info('Embargo expired for FOI Request %d - %s on %s',
                        self.pk, self.title, self.embargo_date())
            self.embargo = False
            self.save()

        return False

    def has_crowdfund(self):
        """Does this request have crowdfunding enabled?"""
        return hasattr(self, 'crowdfund')

    def embargo_date(self):
        """The date this request comes off of embargo"""
        if self.embargo:
            return self.date_embargo

    def public_documents(self):
        """Get a list of public documents attached to this request"""
        # pylint: disable=E1101
        return self.files.filter(access='public').exclude(doc_id='')

    def percent_complete(self):
        """Get percent complete for the progress bar"""
        percents = {'started':   25,  'submitted': 50, 'processed': 75,
                    'fix':       75,  'payment':   75, 'rejected': 100,
                    'no_docs':   100, 'done':     100, 'partial':   90,
                    'abandoned': 100, 'appealing': 75}
        return percents.get(self.status, 0)

    def color_code(self):
        """Get the color code for the current status"""
        processed = 'stop' if self.date_due and date.today() > self.date_due else 'go'
        colors = {'started':   'wait', 'submitted': 'go',   'processed': processed,
                  'fix':       'wait', 'payment':   'wait', 'rejected':  'stop',
                  'no_docs':   'stop', 'done':      'go',   'partial': 'go',
                  'abandoned': 'stop', 'appealing': processed}
        return colors.get(self.status, 'go')

    def first_request(self):
        """Return the first request text"""
        # pylint: disable=E1101
        try:
            return self.communications.all()[0].communication
        except IndexError:
            return ''

    def set_mail_id(self):
        """Set the mail id, which is the unique identifier for the auto mailer system"""
        # pylint: disable=E1101

        # use raw sql here in order to avoid race conditions
        uid = int(md5(self.title.encode('utf8') +
                      datetime.now().isoformat()).hexdigest(), 16) % 10 ** 8
        mail_id = '%s-%08d' % (self.pk, uid)
        cursor = connection.cursor()
        cursor.execute("UPDATE foia_foiarequest "
                       "SET mail_id = CASE WHEN mail_id='' THEN %s ELSE mail_id END "
                       "WHERE id = %s", [mail_id, self.pk])
        transaction.commit_unless_managed()
        # set object's mail id to what is in the database
        self.mail_id = FOIARequest.objects.get(pk=self.pk).mail_id

    def get_mail_id(self):
        """Get the mail id - generate it if it doesn't exist"""
        if not self.mail_id:
            self.set_mail_id()
        return self.mail_id

    def get_other_emails(self):
        """Get the other emails for this request as a list"""
        # Adding blank emails here breaks mailgun backend
        return [e for e in fields.email_separator_re.split(self.other_emails) if e]

    def get_to_who(self):
        """Who communications are to"""
        # pylint: disable=E1101

        if self.agency:
            return self.agency.name
        else:
            return ''

    def get_saved(self):
        """Get the old model that is saved in the db"""

        try:
            return FOIARequest.objects.get(pk=self.pk)
        except FOIARequest.DoesNotExist:
            return None

    def last_comm(self):
        """Return the last communication"""
        # pylint: disable=E1101
        return self.communications.reverse()[0]

    def last_comm_date(self):
        """Return the date of the latest communication or doc or file"""
        # pylint: disable=E1101

        qsets = [self.communications.all().order_by('-date'),
                 self.files.exclude(date=None).order_by('-date')]

        dates = []
        for qset in qsets:
            if qset:
                # convert datetimes to dates
                dates.append(qset[0].date.date() if hasattr(qset[0].date, 'date') else qset[0].date)

        return max(dates) if dates else None

    def update(self, anchor=None):
        """Various actions whenever the request has been updated"""
        # pylint: disable=E1101

        self.updated = True
        self.save()

        for profile in chain(self.followed_by.all(), [self.user.get_profile()]):
            profile.notify(self)

        self.update_dates()

    def submit(self, appeal=False):
        """The request has been submitted.  Notify admin and try to auto submit"""
        # pylint: disable=E1101

        # can email appeal if the agency has an appeal agency which has an email address
        # and can accept emailed appeals
        can_email_appeal = appeal and self.agency and self.agency.appeal_agency and \
                           self.agency.appeal_agency.email and \
                           self.agency.appeal_agency.can_email_appeals

        # update email addresses for the request
        if can_email_appeal:
            self.email = self.agency.appeal_agency.get_email()
            self.other_emails = self.agency.appeal_agency.other_emails
        elif not self.email and self.agency:
            self.email = self.agency.get_email()
            self.other_emails = self.agency.other_emails

        # if the request can be emailed, email it, otherwise send a notice to the admin
        if (self.email and not appeal) or can_email_appeal:
            self.status = 'processed' if not appeal else 'appealing'
            self._send_email()
            self.update_dates()
        else:
            self.status = 'submitted'
            notice = 'NEW' if self.communications.count() == 1 else 'UPDATED'
            notice = 'APPEAL' if appeal else notice
            send_mail('[%s] Freedom of Information Request: %s' % (notice, self.title),
                      render_to_string('foia/admin_mail.txt',
                                       {'request': self, 'appeal': appeal}),
                      'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)
        self.save()

        # whether it is automailed or not, notify the followers (but not the owner)
        send_data = []
        for profile in self.followed_by.all():
            link = AuthKey.objects.wrap_url(self.get_absolute_url(), uid=profile.user.pk)
            msg = render_to_string('foia/mail.txt',
                {'name': profile.user.get_full_name(),
                 'title': self.title,
                 'status': self.get_status_display(),
                 'link': link,
                 'follow': self.user != profile.user})
            send_data.append(('[MuckRock] FOI request "%s" has been updated' % self.title,
                              msg, 'info@muckrock.com', [profile.user.email]))

        send_mass_mail(send_data, fail_silently=False)

    def followup(self):
        """Send a follow up email for this request"""
        # pylint: disable=E1101

        FOIACommunication.objects.create(
            foia=self, from_who='MuckRock.com', to_who=self.get_to_who(),
            date=datetime.now(), response=False, full_html=False,
            communication=render_to_string('foia/followup.txt', {'request': self}))

        if not self.email and self.agency:
            self.email = self.agency.get_email()
            self.other_emails = self.agency.other_emails
            self.save()

        if self.email:
            self._send_email()
        else:
            self.status = 'submitted'
            self.save()
            send_mail('[FOLLOWUP] Freedom of Information Request: %s' % self.title,
                      render_to_string('foia/admin_mail.txt', {'request': self}),
                      'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

        # Do not self.update() here for now to avoid excessive emails
        self.update_dates()

    def _send_email(self):
        """Send an email of the request to its email address"""
        # pylint: disable=E1101
        # self.email should be set before calling this method

        from_addr = 'fax' if self.email.endswith('faxaway.com') else self.get_mail_id()
        if self.tracking_id:
            subject = 'Follow up to Freedom of Information Request #%s' % self.tracking_id
        elif self.communications.count() > 1:
            subject = 'Follow up to Freedom of Information Request: %s' % self.title
        else:
            subject = 'Freedom of Information Request: %s' % self.title

        cc_addrs = self.get_other_emails()
        msg = EmailMessage(subject=subject,
                           body=render_to_string('foia/request.txt', {'request': self}),
                           from_email='%s@%s' % (from_addr, MAILGUN_SERVER_NAME),
                           to=[self.email],
                           bcc=cc_addrs + ['requests@muckrock.com'],
                           headers={'Cc': ','.join(cc_addrs)}) 
        # atach all files from the latest communication
        for file_ in self.communications.reverse()[0].files.all():
            msg.attach(file_.name(), file_.ffile.read())
        msg.send(fail_silently=False)

    def update_dates(self):
        """Set the due date, follow up date and days until due attributes"""
        # pylint: disable=E1101

        cal = self.jurisdiction.get_calendar()

        # first submit
        if not self.date_submitted:
            self.date_submitted = date.today()
            days = self.jurisdiction.get_days()
            if days:
                self.date_due = cal.business_days_from(date.today(), days)

        # updated from mailgun without setting status or submitted
        if self.status == 'processed':

            # unpause the count down
            if self.days_until_due is not None:
                self.date_due = cal.business_days_from(date.today(), self.days_until_due)
                self.days_until_due = None

            self._update_followup_date()

        # if we are no longer waiting on the agency, do not follow up
        if self.status != 'processed' and self.date_followup:
            self.date_followup = None

        # if we need to respond, pause the count down until we do
        if self.status in ['fix', 'payment'] and self.date_due:
            last_date = self.last_comm_date()
            if not last_date:
                last_date = date.today()
            self.days_until_due = cal.business_days_between(last_date, self.date_due)
            self.date_due = None

        self.save()

    def _update_followup_date(self):
        """Update the follow up date"""
        try:
            new_date = self.last_comm().date.date() + timedelta(self._followup_days())
            if self.date_due and self.date_due > new_date:
                new_date = self.date_due

            if not self.date_followup or self.date_followup < new_date:
                self.date_followup = new_date

        except IndexError:
            # This request has no communications at the moment, cannot asign a follow up date
            pass

    def _followup_days(self):
        """How many days do we wait until we follow up?"""
        # pylint: disable=E1101
        if self.jurisdiction and self.jurisdiction.level == 'f':
            return 30
        else:
            return 15

    def update_tags(self, tags):
        """Update the requests tags"""
        # pylint: disable=W0142

        tag_set = set()
        for tag in tags.split(','):
            tag = Tag.normalize(tag)
            if not tag:
                continue
            new_tag, _ = Tag.objects.get_or_create(name=tag, defaults={'user': self.user})
            tag_set.add(new_tag)
        self.tags.set(*tag_set)

    def actions(self, user):
        """What actions may the given user take on this Request"""
        # pylint: disable=E1101

        kwargs = {'jurisdiction': self.jurisdiction.slug, 'jidx': self.jurisdiction.pk,
                  'idx': self.pk, 'slug': self.slug}

        side_actions = [
            (user.is_staff,
                reverse('admin:foia_foiarequest_change', args=(self.pk,)), 'Admin'),
            (self.user == user and self.is_editable(),
                reverse('foia-update', kwargs=kwargs), 'Update'),
            (self.user == user and not self.is_editable() and user.get_profile().can_embargo(),
                reverse('foia-embargo', kwargs=kwargs), 'Update Embargo'),
            (self.user == user and self.is_deletable(),
                reverse('foia-delete', kwargs=kwargs), 'Delete'),
            (user.is_staff,
                reverse('foia-admin-fix', kwargs=kwargs), 'Admin Fix'),
            (self.user == user and self.is_payable(),
                reverse('foia-pay', kwargs=kwargs), 'Pay'),
            (self.user == user and self.is_payable(),
                reverse('foia-crowdfund', kwargs=kwargs), 'Crowdfund'),
            (self.public_documents(), '#', 'Embed this Document'),
            (user.is_authenticated() and self.user != user,
                reverse('foia-follow', kwargs=kwargs),
                'Unfollow' if user.is_authenticated() and self.followed_by.filter(user=user)
                           else 'Follow'),
            ]

        bottom_actions = [
            (self.user == user,
                'Follow Up', 'Send a message directly to the agency'),
            (self.user == user,
                'Get Advice', "Get answers to your question from Muckrock's FOIA expert community"),
            (user.is_authenticated(),
                'Problem?', "Something broken, buggy, or off?  Let us know and we'll fix it"),
            (self.user == user and self.is_appealable(),
                'Appeal', 'Submit an appeal'),
            ]

        side_action_links = [{'link': link, 'label': label,
                              'id': 'opener' if label == 'Embed this Document' else ''}
                             for pred, link, label in side_actions if pred]
        bottom_action_links = [{'label': label, 'title': title}
                               for pred, label, title in bottom_actions if pred]

        return {'side': side_action_links, 'bottom': bottom_action_links}

    def total_pages(self):
        """Get the total number of pages for this request"""
        # pylint: disable=E1101
        pages = self.files.aggregate(Sum('pages'))['pages__sum']
        if pages is None:
            return 0
        return pages


    class Meta:
        # pylint: disable=R0903
        ordering = ['title']
        verbose_name = 'FOIA Request'


class FOIAMultiRequest(models.Model):
    """A Freedom of Information Act request"""
    # pylint: disable=R0904
    # pylint: disable=R0902

    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS[:2])
    embargo = models.BooleanField()
    requested_docs = models.TextField(blank=True)
    agencies = models.ManyToManyField(Agency, related_name='agencies', blank=True, null=True)

    tags = TaggableManager(through=TaggedItemBase, blank=True)

    foia_type = 'multi'

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('foia-multi-update', [], {'slug': self.slug, 'idx': self.pk})

    def submit(self):
        """Submit the multi request to all of the agencies"""
        # pylint: disable=E1101
        agencies = self.agencies.all()
        for agency in agencies:
            # make a copy of the foia (and its communication) for each agency
            title = '%s (%s)' % (self.title, agency.name)
            template = get_template('request_templates/none.txt')
            context = Context({'document_request': self.requested_docs,
                               'jurisdiction': agency.jurisdiction,
                               'user': self.user})
            foia_request = template.render(context).split('\n', 1)[1].strip()

            new_foia = FOIARequest.objects.create(
                user=self.user, status='started', title=title, slug=slugify(title),
                jurisdiction=agency.jurisdiction, agency=agency, embargo=self.embargo,
                requested_docs=self.requested_docs, description=self.requested_docs)

            FOIACommunication.objects.create(
                    foia=new_foia, from_who=new_foia.user.get_full_name(),
                    to_who=new_foia.get_to_who(), date=datetime.now(), response=False,
                    full_html=False, communication=foia_request)

            new_foia.submit()
        self.delete()

    def color_code(self):
        """Get the color code for the current status"""
        colors = {'started':   'wait', 'submitted': 'go'}
        return colors.get(self.status, 'go')

    class Meta:
        # pylint: disable=R0903
        ordering = ['title']
        verbose_name = 'FOIA Multi-Request'


class FOIACommunication(models.Model):
    """A single communication of a FOIA request"""

    foia = models.ForeignKey(FOIARequest, related_name='communications')
    from_who = models.CharField(max_length=255)
    to_who = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField()
    response = models.BooleanField(help_text='Is this a response (or a request)?')
    full_html = models.BooleanField()
    communication = models.TextField(blank=True)
    # what status this communication should set the request to - used for machine learning
    status = models.CharField(max_length=10, choices=STATUS, blank=True, null=True)

    def __unicode__(self):
        return '%s: %s...' % (self.date.strftime('%m/%d/%y'), self.communication[:80])

    def anchor(self):
        """Anchor name"""
        return 'comm-%d' % self.pk

    class Meta:
        # pylint: disable=R0903
        ordering = ['foia', 'date']
        verbose_name = 'FOIA Communication'


class FOIANote(models.Model):
    """A private note on a FOIA request"""

    foia = models.ForeignKey(FOIARequest, related_name='notes')
    date = models.DateTimeField()
    note = models.TextField()

    class Meta:
        # pylint: disable=R0903
        ordering = ['foia', 'date']
        verbose_name = 'FOIA Note'


class FOIAFile(models.Model):
    """An arbitrary file attached to a FOIA request"""

    access = (('public', 'Public'), ('private', 'Private'), ('organization', 'Organization'))

    # pylint: disable=E1101
    foia = models.ForeignKey(FOIARequest, related_name='files', blank=True, null=True)
    comm = models.ForeignKey(FOIACommunication, related_name='files', blank=True, null=True)
    ffile = models.FileField(upload_to='foia_files', verbose_name='File', max_length=255)
    title = models.CharField(max_length=70)
    date = models.DateTimeField(null=True)
    source = models.CharField(max_length=70, blank=True)
    description = models.TextField(blank=True)
    # for doc cloud only
    access = models.CharField(max_length=12, default='public', choices=access)
    doc_id = models.SlugField(max_length=80, blank=True, editable=False)
    pages = models.PositiveIntegerField(default=0, editable=False)

    def __unicode__(self):
        return self.title

    def name(self):
        """Return the basename of the file"""
        return os.path.basename(self.ffile.name)

    def is_doccloud(self):
        """Is this a file doc cloud can support"""

        _, ext = os.path.splitext(self.ffile.name)
        return ext.lower() in ['.pdf', '.doc', '.docx']

    def get_thumbnail(self, size='thumbnail', page=1):
        """Get the url to the thumbnail image"""
        match = re.match('^(\d+)-(.*)$', self.doc_id)
        mimetypes = {
            'avi': 'file-video.png',
            'bmp': 'file-image.png',
            'csv': 'file-spreadsheet.png',
            'gif': 'file-image.png',
            'jpg': 'file-image.png',
            'mp3': 'file-audio.png',
            'mpg': 'file-video.png',
            'png': 'file-image.png',
            'ppt': 'file-presentation.png',
            'pptx': 'file-presentation.png',
            'tif': 'file-image.png',
            'wav': 'file-audio.png',
            'xls': 'file-spreadsheet.png',
            'xlsx': 'file-spreadsheet.png',
            'zip': 'file-archive.png',
        }

        if match and self.pages > 0 and self.access == 'public':
            return '//s3.amazonaws.com/s3.documentcloud.org/documents/'\
                   '%s/pages/%s-p%d-%s.gif' % (match.groups() + (page, size))
        else:
            ext = os.path.splitext(self.name())[1][1:]
            filename = mimetypes.get(ext, 'file-document.png')
            return '%simg/%s' % (STATIC_URL, filename)

    def get_medium_thumbnail(self):
        """Convenient function for template"""
        return self.get_thumbnail('small')

    def get_foia(self):
        """Get FOIA - self.foia should be refactored out"""
        if self.foia:
            return self.foia
        if self.comm and self.comm.foia:
            return self.comm.foia

    def is_viewable(self, user):
        """Is this document viewable to user"""
        return self.access == 'public' and self.foia.is_viewable(user)

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.is_viewable(AnonymousUser())

    def anchor(self):
        """Anchor name"""
        return 'file-%d' % self.pk

    class Meta:
        # pylint: disable=R0903
        verbose_name = 'FOIA Document File'
        ordering = ['comm', 'date']

