"""
Models for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.core.mail import send_mail, send_mass_mail
from django.db import models, connection, transaction
from django.db.models import Q
from django.template.loader import render_to_string

from lamson.mail import MailResponse

from datetime import datetime, date, timedelta
from hashlib import md5
from itertools import chain
from taggit.managers import TaggableManager
import os
import re

from business_days.business_days import calendars
from muckrock.models import ChainableManager
from settings import relay, LAMSON_ROUTER_HOST, LAMSON_ACTIVATE
from tags.models import Tag, TaggedItemBase
import fields

FOLLOWUP_DAYS = 15

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
                                ~Q(embargo=True, date_embargo__gt=datetime.today())))
        else:
            # anonymous user, filter out drafts and embargoes
            return self.exclude(status='started') \
                       .exclude(embargo=True, date_embargo=None) \
                       .exclude(embargo=True, date_embargo__gt=datetime.today())

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


class FOIARequest(models.Model):
    """A Freedom of Information Act request"""
    # pylint: disable-msg=R0904
    # pylint: disable-msg=R0902

    status = (
        ('started', 'Draft'),
        ('submitted', 'Processing'),
        ('processed', 'Awaiting Response'),
        ('fix', 'Fix Required'),
        ('payment', 'Payment Required'),
        ('rejected', 'Rejected'),
        ('no_docs', 'No Responsive Documents'),
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
    days_until_due = models.IntegerField(blank=True, null=True)
    date_followup = models.DateField(blank=True, null=True)
    embargo = models.BooleanField()
    date_embargo = models.DateField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    description = models.TextField(blank=True)
    featured = models.BooleanField()
    tracker = models.BooleanField()
    sidebar_html = models.TextField(blank=True)
    tracking_id = models.CharField(blank=True, max_length=255)
    mail_id = models.CharField(blank=True, max_length=255, editable=False)
    updated = models.BooleanField()
    email = models.EmailField(blank=True)
    other_emails = fields.EmailsListField(blank=True, max_length=255)

    objects = FOIARequestManager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

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
        return self.status == 'started'

    def is_fixable(self):
        """Can this request be ammended by the user?"""
        return self.status == 'fix'

    def is_appealable(self):
        """Can this request be appealed by the user?"""
        return self.status == 'rejected'

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
            self.embargo = False
            self.save()

        return False

    def embargo_date(self):
        """The date this request comes off of embargo"""
        if self.embargo:
            return self.date_embargo

    def public_documents(self):
        """Get a list of public documents attached to this request"""
        # pylint: disable-msg=E1101
        return self.documents.filter(access='public').exclude(doc_id='')

    def percent_complete(self):
        """Get percent complete for the progress bar"""
        percents = {'started': 25,  'submitted': 50, 'processed': 75,
                    'fix':     75,  'payment':   75, 'rejected': 100,
                    'no_docs': 100, 'done':     100, 'partial':   90}
        return percents[self.status]

    def color_code(self):
        """Get the color code for the current status"""
        processed = 'stop' if self.date_due and date.today() > self.date_due else 'go'
        colors = {'started': 'wait', 'submitted': 'go',   'processed': processed,
                  'fix':     'wait', 'payment':   'wait', 'rejected':  'stop',
                  'no_docs': 'stop', 'done':      'go',   'partial': 'go'}
        return colors[self.status]

    def first_request(self):
        """Return the first request text"""
        # pylint: disable-msg=E1101
        return self.communications.all()[0].communication

    def get_communications(self, user):
        """Get communications and documents to display on details page"""
        # pylint: disable-msg=E1101
        comms = self.communications.all()
        docs = self.documents.exclude(date=None)
        files = self.files.exclude(date=None)
        if self.user != user and not user.is_staff:
            docs = docs.filter(access='public')
        display_comms = list(comms) + list(docs) + list(files)
        display_comms.sort(key=lambda x: x.date)
        return display_comms

    def set_mail_id(self):
        """Set the mail id, which is the unique identifier for the auto mailer system"""

        # use raw sql here in order to avoid race conditions
        uid = int(md5(self.title + datetime.now().isoformat()).hexdigest(), 16) % 10 ** 8
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
        return fields.email_separator_re.split(self.other_emails)

    def get_to_who(self):
        """Who communications are to"""
        # pylint: disable-msg=E1101

        if self.agency and self.email:
            to_who = '%s <%s>' % (self.agency.name, self.email)
        elif self.agency and self.agency.email:
            to_who = '%s <%s>' % (self.agency.name, self.agency.email)
        elif self.agency:
            to_who = self.agency.name
        else:
            to_who = ''
        return to_who[:255]

    def get_saved(self):
        """Get the old model that is saved in the db"""

        try:
            return FOIARequest.objects.get(pk=self.pk)
        except FOIARequest.DoesNotExist:
            return None

    def last_comm(self):
        """Return the last communication"""
        # pylint: disable-msg=E1101
        return self.communications.reverse()[0]

    def last_comm_date(self):
        """Return the date of the latest communication or doc or file"""
        # pylint: disable-msg=E1101

        qsets = [self.communications.all().order_by('-date'),
                 self.documents.exclude(date=None).order_by('-date'),
                 self.files.exclude(date=None).order_by('-date')]

        dates = []
        for qset in qsets:
            if qset:
                # convert datetimes to dates
                dates.append(qset[0].date.date() if hasattr(qset[0].date, 'date') else qset[0].date)

        return max(dates) if dates else None

    def update(self, anchor=None):
        """Various actions whenever the request has been updated"""
        # pylint: disable-msg=E1101

        # mark the request as updated and notify the user
        if not self.updated:
            self.updated = True
            self.save()

            link = self.get_absolute_url()
            if anchor:
                link += '#' + anchor

            send_data = []
            for profile in chain(self.followed_by.all(), [self.user.get_profile()]):
                msg = render_to_string('foia/mail.txt',
                    {'name': profile.user.get_full_name(),
                     'title': self.title,
                     'status': self.get_status_display(),
                     'link': link,
                     'follow': self.user != profile.user})
                send_data.append(('[MuckRock] FOI request "%s" has been updated' % self.title,
                                  msg, 'info@muckrock.com', [profile.user.email]))

            send_mass_mail(send_data, fail_silently=False)

        self.update_dates()

    def submit(self, appeal=False):
        """The request has been submitted.  Notify admin and try to auto submit"""
        # pylint: disable-msg=E1101

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
        if LAMSON_ACTIVATE and ((self.email and not appeal) or can_email_appeal):
            self.status = 'processed'
            self._send_email()
            self.update_dates()
            if not self.date_submitted:
                self.date_submitted = date.today()
                days = self.jurisdiction.get_days()
                if days:
                    cal = calendars[self.jurisdiction.legal()]
                    self.date_due = cal.business_days_from(date.today(), days)
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
            msg = render_to_string('foia/mail.txt',
                {'name': profile.user.get_full_name(),
                 'title': self.title,
                 'status': self.get_status_display(),
                 'link': self.get_absolute_url(),
                 'follow': self.user != profile.user})
            send_data.append(('[MuckRock] FOI request "%s" has been updated' % self.title,
                              msg, 'info@muckrock.com', [profile.user.email]))

        send_mass_mail(send_data, fail_silently=False)

    def followup(self):
        """Send a follow up email for this request"""
        # pylint: disable-msg=E1101

        comm = FOIACommunication.objects.create(
                foia=self, from_who=self.user.get_full_name(), to_who=self.get_to_who(),
                date=datetime.now(), response=False, full_html=False,
                communication=render_to_string('foia/followup.txt', {'request': self}))

        if not self.email and self.agency:
            self.email = self.agency.get_email()
            self.other_emails = self.agency.other_emails
            self.save()

        if self.email and LAMSON_ACTIVATE:
            self._send_email()
        else:
            self.status = 'submitted'
            self.save()
            send_mail('[FOLLOWUP] Freedom of Information Request: %s' % self.title,
                      render_to_string('foia/admin_mail.txt', {'request': self}),
                      'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

        self.update(comm.anchor())

    def _send_email(self):
        """Send an email of the request to it's email address"""
        # pylint: disable-msg=E1101
        # self.email should be set before calling this method

        from_addr = 'fax' if self.email.endswith('faxaway.com') else self.get_mail_id()
        if self.tracking_id:
            subject = 'Follow up to Freedom of Information Request #%s' % self.tracking_id
        elif self.communications.count() > 1:
            subject = 'Follow up to Freedom of Information Request: %s' % self.title
        else:
            subject = 'Freedom of Information Request: %s' % self.title
        msg = MailResponse(From='%s@%s' % (from_addr, LAMSON_ROUTER_HOST),
                           To=self.email,
                           Subject=subject,
                           Body=render_to_string('foia/request.txt', {'request': self}))
        cc_addrs = self.get_other_emails()
        if cc_addrs:
            msg['cc'] = ','.join(cc_addrs)
        relay.deliver(msg, To=[self.email, 'requests@muckrock.com'] + cc_addrs)

    def update_dates(self):
        """Set the due date, follow up date and days until due attributes"""
        # pylint: disable-msg=E1101

        cal = calendars.get(self.jurisdiction.legal())
        if not cal:
            send_mail('%s needs a calendar' % self.jurisdiction, '', 'info@muckrock.com',
                      ['requests@muckrock.com'], fail_silently=False)
            cal = calendars['USA']

        # first submit
        if not self.date_submitted:
            self.date_submitted = date.today()
            days = self.jurisdiction.get_days()
            if days:
                self.date_due = cal.business_days_from(date.today(), days)

        # updated from lamson without setting status or submitted
        if self.status == 'processed':

            # unpause the count down
            if self.days_until_due is not None:
                self.date_due = cal.business_days_from(date.today(), self.days_until_due)
                self.days_until_due = None

            # update follow up date
            if self.date_due:
                self.date_followup = max(self.date_due,
                                         self.last_comm().date.date() + timedelta(FOLLOWUP_DAYS))
            else:
                self.date_followup = self.last_comm().date.date() + timedelta(FOLLOWUP_DAYS)

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

    def update_tags(self, tags):
        """Update the requests tags"""
        # pylint: disable-msg=W0142

        html_remove = dict((ord(c), None) for c in ['<', '>', '&', '"', "'"])

        tag_set = set()
        for tag in tags.split(','):
            tag = tag.translate(html_remove)
            if not tag:
                continue
            new_tag, _ = Tag.objects.get_or_create(name=tag, defaults={'user': self.user})
            tag_set.add(new_tag)
        self.tags.set(*tag_set)

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['title']
        verbose_name = 'FOIA Request'


class FOIACommunication(models.Model):
    """A single communication of a FOIA request"""

    status = (
        ('processed', 'Awaiting Response'),
        ('fix', 'Fix Required'),
        ('payment', 'Payment Required'),
        ('rejected', 'Rejected'),
        ('no_docs', 'No Responsive Documents'),
        ('done', 'Completed'),
        ('partial', 'Partially Completed'),
    )

    foia = models.ForeignKey(FOIARequest, related_name='communications')
    from_who = models.CharField(max_length=255)
    to_who = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField()
    response = models.BooleanField(help_text='Is this a response (or a request)?')
    full_html = models.BooleanField()
    communication = models.TextField()
    # what status this communication should set the request to - used for machine learning
    status = models.CharField(max_length=10, choices=status, blank=True, null=True)

    class_name = 'FOIACommunication'

    def anchor(self):
        """Anchor name"""
        return 'comm-%d' % self.pk

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['foia', 'date']
        verbose_name = 'FOIA Communication'


class FOIANote(models.Model):
    """A private note on a FOIA request"""

    foia = models.ForeignKey(FOIARequest, related_name='notes')
    date = models.DateTimeField()
    note = models.TextField()

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['foia', 'date']
        verbose_name = 'FOIA Note'


class FOIADocument(models.Model):
    """A DocumentCloud document attached to a FOIA request"""

    access = (('public', 'Public'), ('private', 'Private'), ('organization', 'Organization'))

    # pylint: disable-msg=E1101
    foia = models.ForeignKey(FOIARequest, related_name='documents')
    document = models.FileField(upload_to='foia_documents')
    title = models.CharField(max_length=70)
    source = models.CharField(max_length=70)
    description = models.TextField(blank=True)
    access = models.CharField(max_length=12, choices=access)
    doc_id = models.SlugField(max_length=80, editable=False)
    pages = models.PositiveIntegerField(default=0, editable=False)
    date = models.DateTimeField(null=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """The url for this object"""
        return '%s#%s' % (self.foia.get_absolute_url(), self.doc_id)

    def get_thumbnail(self, size='thumbnail', page=1):
        """Get the url to the thumbnail image"""
        match = re.match('^(\d+)-(.*)$', self.doc_id)

        if match and self.access == 'public':
            return 'http://s3.documentcloud.org/documents/'\
                   '%s/pages/%s-p%d-%s.gif' % (match.groups() + (page, size))
        else:
            return '/static/img/report.png'

    def get_medium_thumbnail(self):
        """Convenient function for template"""
        return self.get_thumbnail('small')

    def is_viewable(self, user):
        """Is this document viewable to user"""
        return self.access == 'public' and self.foia.is_viewable(user)

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.is_viewable(AnonymousUser())

    # following methods are to make this quack like a communication for display on the details page
    response = True
    full_html = False
    class_name = 'FOIADocument'

    def from_who(self):
        """To quack like a communication"""
        return self.source

    def communication(self):
        """To quack like a communication"""
        return self.description

    def anchor(self):
        """Anchor name"""
        return 'doc-%d' % self.pk

    class Meta:
        # pylint: disable-msg=R0903
        verbose_name = 'FOIA DocumentCloud Document'


class FOIADocTopViewed(models.Model):
    """Keep track of the top 5 most viewed requests for the front page"""

    req = models.ForeignKey(FOIARequest, null=True)
    rank = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        # pylint: disable-msg=R0903
        ordering = ['rank']
        verbose_name = 'FOIA Top Viewed Request'


class FOIAFile(models.Model):
    """An arbitrary file attached to a FOIA request"""
    # pylint: disable-msg=E1101
    foia = models.ForeignKey(FOIARequest, related_name='files')
    ffile = models.FileField(upload_to='foia_files')
    date = models.DateTimeField(null=True)
    source = models.CharField(max_length=70, blank=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return 'File: %s' % self.ffile.name

    def name(self):
        """Return the basename of the file"""
        return os.path.basename(self.ffile.name)

    # following methods are to make this quack like a communication for display on the details page
    response = True
    full_html = False
    class_name = 'FOIAFile'

    def from_who(self):
        """To quack like a communication"""
        return self.source

    def communication(self):
        """To quack like a communication"""
        return self.description

    def anchor(self):
        """Anchor name"""
        return 'file-%d' % self.pk

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
    hidden = models.BooleanField(default=False)
    days = models.PositiveSmallIntegerField(blank=True, null=True)

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

    def get_days(self):
        """How many days does an agency have to reply?"""
        # pylint: disable-msg=E1101
        if self.level == 'l':
            return self.parent.days
        else:
            return self.days

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
        # pylint: disable-msg=R0903
        verbose_name_plural = 'agencies'

