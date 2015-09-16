# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models import Q, Sum
from django.template.defaultfilters import escape, linebreaks, slugify
from django.template.loader import render_to_string

from datetime import datetime, date, timedelta
from hashlib import md5
from itertools import chain
from taggit.managers import TaggableManager
from unidecode import unidecode
import logging

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import MAILGUN_SERVER_NAME
from muckrock.tags.models import Tag, TaggedItemBase
from muckrock import task
from muckrock import fields

logger = logging.getLogger(__name__)

class FOIARequestQuerySet(models.QuerySet):
    """Object manager for FOIA requests"""
    # pylint: disable=too-many-public-methods

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
        return self.filter(status__in=['ack', 'processed'], date_due__lt=date.today())

    def get_manual_followup(self):
        """Get old requests which require us to follow up on with the agency"""

        return [
            f for f in self.get_overdue()
            if f.communications.all().reverse()[0].date + timedelta(15) < datetime.now()
        ]

    def get_followup(self):
        """Get requests that need follow up emails sent"""
        return self.filter(status__in=['ack', 'processed'],
                           date_followup__lte=date.today(),
                           disable_autofollowups=False)

    def get_open(self):
        """Get requests which we are awaiting a response from"""
        return self.filter(status__in=['ack', 'processed', 'appealing'])

    def get_undated(self):
        """Get requests which have an undated file"""
        return self.filter(~Q(files=None) & Q(files__date=None)).distinct()


STATUS = (
    ('started', 'Draft'),
    ('submitted', 'Processing'),
    ('ack', 'Awaiting Acknowledgement'),
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

class Action():
    """A helper class to provide interfaces for request actions"""
    # pylint: disable=too-many-arguments
    def __init__(self, test=None, link=None, title=None, action=None, desc=None, class_name=None):
        self.test = test
        self.link = link
        self.title = title
        self.action = action
        self.desc = desc
        self.class_name = class_name

    def is_possible(self):
        """Is this action possible given the current context?"""
        return self.test


class FOIARequest(models.Model):
    """A Freedom of Information Act request"""
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

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
    date_estimate = models.DateField(blank=True, null=True,
            verbose_name='Estimated Date Completed')
    embargo = models.BooleanField(default=False)
    date_embargo = models.DateField(blank=True, null=True)
    permanent_embargo = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=14, decimal_places=2, default='0.00')
    requested_docs = models.TextField(blank=True)
    description = models.TextField(blank=True)
    featured = models.BooleanField(default=False)
    tracker = models.BooleanField(default=False)
    sidebar_html = models.TextField(blank=True)
    tracking_id = models.CharField(blank=True, max_length=255)
    mail_id = models.CharField(blank=True, max_length=255, editable=False)
    updated = models.BooleanField(default=False)
    email = models.EmailField(blank=True)
    other_emails = fields.EmailsListField(blank=True, max_length=255)
    times_viewed = models.IntegerField(default=0)
    disable_autofollowups = models.BooleanField(default=False)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)
    block_incoming = models.BooleanField(
        default=False,
        help_text=('Block emails incoming to this request from '
                   'automatically being posted on the site')
    )

    read_collaborators = models.ManyToManyField(
        User,
        related_name='read_access',
        blank=True,
    )
    edit_collaborators = models.ManyToManyField(
        User,
        related_name='edit_access',
        blank=True,
    )

    objects = FOIARequestQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    foia_type = 'foia'

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        """The url for this object"""
        return ('foia-detail', [], {
            'jurisdiction': self.jurisdiction.slug,
            'jidx': self.jurisdiction.pk,
            'slug': self.slug,
            'idx': self.pk
        })

    def save(self, *args, **kwargs):
        """Normalize fields before saving"""
        self.slug = slugify(self.slug)
        self.title = self.title.strip()
        super(FOIARequest, self).save(*args, **kwargs)

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
        return self.price > 0 and not self.has_crowdfund()

    def get_stripe_amount(self):
        """Output a Stripe Checkout formatted price"""
        return int(self.price*105)

    def is_deletable(self):
        """Can this request be deleted?"""
        return self.status == 'started'

    def is_viewable(self, user):
        """Is this request viewable?"""
        # pylint: disable=unexpected-keyword-arg
        return user.is_staff or self.user == user or \
            self.read_collaborators.filter(pk=user.pk).exists() or \
            self.edit_collaborators.filter(pk=user.pk).exists() or \
            (self.status != 'started' and not self.is_embargo())

    def is_public(self):
        """Is this document viewable to everyone"""
        return self.is_viewable(AnonymousUser())

    def is_embargo(self, save=True):
        """Is this request currently on an embargo?"""
        if not self.embargo:
            return False

        if self.is_permanently_embargoed() or not self.embargo_date() or \
                date.today() < self.embargo_date():
            return True

        if save:
            logger.info('Embargo expired for FOI Request %d - %s on %s',
                        self.pk, self.title, self.embargo_date())
            self.embargo = False
            self.save()

        return False

    def embargo_date(self):
        """The date this request comes off of embargo"""
        if self.embargo:
            return self.date_embargo

    def is_permanently_embargoed(self):
        """The request is permanently embargoed"""
        if self.embargo:
            return self.permanent_embargo

    # Request Sharing and Permissions

    ## Editors

    def has_editor(self, user):
        """Checks whether the given user is an editor."""
        user_is_editor = False
        if self.edit_collaborators.filter(pk=user.pk).exists():
            user_is_editor = True
        return user_is_editor

    def add_editor(self, user):
        """Grants the user permission to edit this request."""
        if not self.has_editor(user):
            self.edit_collaborators.add(user)
            self.save()
        return

    def remove_editor(self, user):
        """Revokes the user's permission to edit this request."""
        if self.has_editor(user):
            self.edit_collaborators.remove(user)
            self.save()
        return

    def editable_by(self, user):
        """Can this user edit this request"""
        return self.user == user or self.has_editor(user) or user.is_staff

    ## Viewers

    def has_viewer(self, user):
        """Checks whether the given user is a viewer."""
        user_is_viewer = False
        if self.read_collaborators.filter(pk=user.pk).exists():
            user_is_viewer = True
        return user_is_viewer

    def add_viewer(self, user):
        """Grants the user permission to view this request."""
        if not self.has_viewer(user):
            self.read_collaborators.add(user)
            self.save()
        return

    def has_crowdfund(self):
        """Does this request have crowdfunding enabled?"""
        return hasattr(self, 'crowdfund')

    def public_documents(self):
        """Get a list of public documents attached to this request"""
        return self.files.filter(access='public')

    def percent_complete(self):
        """Get percent complete for the progress bar"""
        percents = {'started':   25, 'submitted':  50, 'ack':       65,
                    'processed': 75, 'fix':        75, 'payment':   75,
                    'rejected': 100, 'no_docs':   100, 'done':     100,
                    'partial':   90, 'abandoned': 100, 'appealing': 75}
        return percents.get(self.status, 0)

    def color_code(self):
        """Get the color code for the current status"""
        # pylint: disable=bad-whitespace
        code_stop = 'failure'
        code_wait = ''
        code_go = 'success'
        code_processed = code_stop if self.date_due and date.today() > self.date_due else code_go
        colors = {'started':   code_wait, 'submitted': code_go,   'code_processed': code_processed,
                  'fix':       code_wait, 'payment':   code_wait, 'rejected':  code_stop,
                  'no_docs':   code_stop, 'done':      code_go,   'partial': code_go,
                  'abandoned': code_stop, 'appealing': code_processed, 'ack': code_processed}
        return colors.get(self.status, code_wait)

    def first_request(self):
        """Return the first request text"""
        try:
            return self.communications.all()[0].communication
        except IndexError:
            return ''

    def set_mail_id(self):
        """Set the mail id, which is the unique identifier for the auto mailer system"""
        # pylint: disable=no-member

        # use raw sql here in order to avoid race conditions
        uid = int(md5(self.title.encode('utf8') +
                      datetime.now().isoformat()).hexdigest(), 16) % 10 ** 8
        mail_id = '%s-%08d' % (self.pk, uid)
        cursor = connection.cursor()
        cursor.execute("UPDATE foia_foiarequest "
                       "SET mail_id = CASE WHEN mail_id='' THEN %s ELSE mail_id END "
                       "WHERE id = %s", [mail_id, self.pk])
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
        # pylint: disable=no-member

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
        # pylint: disable=no-member
        return self.communications.reverse()[0]

    def last_comm_date(self):
        """Return the date of the latest communication or doc or file"""
        # pylint: disable=no-member

        qsets = [self.communications.all().order_by('-date'),
                 self.files.exclude(date=None).order_by('-date')]

        dates = []
        for qset in qsets:
            if qset:
                # convert datetimes to dates
                dates.append(qset[0].date.date() if hasattr(qset[0].date, 'date') else qset[0].date)

        return max(dates) if dates else None

    def latest_response(self):
        """How many days since the last response"""
        # pylint: disable=no-member
        responses = self.communications.filter(response=True).order_by('-date')
        if responses:
            return (date.today() - responses[0].date.date()).days

    def update(self, anchor=None):
        """Various actions whenever the request has been updated"""
        # pylint: disable=no-member
        # pylint: disable=unused-argument
        # Do something with anchor

        self.updated = True
        self.save()

        for profile in chain(self.followed_by.all(), [self.user.profile]):
            if self.is_viewable(profile.user):
                profile.notify(self)

        self.update_dates()

    def submit(self, appeal=False, snail=False):
        """The request has been submitted.  Notify admin and try to auto submit"""
        # pylint: disable=no-member

        # can email appeal if the agency has an appeal agency which has an email address
        # and can accept emailed appeals
        can_email_appeal = appeal and self.agency and \
            self.agency.appeal_agency and self.agency.appeal_agency.email and \
            self.agency.appeal_agency.can_email_appeals

        # update email addresses for the request
        if can_email_appeal:
            self.email = self.agency.appeal_agency.get_email()
            self.other_emails = self.agency.appeal_agency.other_emails
        elif not self.email and self.agency:
            self.email = self.agency.get_email()
            self.other_emails = self.agency.other_emails

        # if agency isnt approved, do not email or snail mail
        # it will be handled after agency is approved
        approved_agency = self.agency and self.agency.approved
        can_email = self.email and not appeal
        comm = self.last_comm()

        # if the request can be emailed, email it, otherwise send a notice to the admin
        if not snail and approved_agency and (can_email or can_email_appeal):
            if appeal:
                self.status = 'appealing'
            elif self.has_ack():
                self.status = 'processed'
            else:
                self.status = 'ack'
            self._send_email()
            self.update_dates()
        elif approved_agency:
            # snail mail it
            self.status = 'submitted'
            notice = 'n' if self.communications.count() == 1 else 'u'
            notice = 'a' if appeal else notice
            comm.delivered = 'mail'
            comm.save()
            task.models.SnailMailTask.objects.create(category=notice, communication=comm)
        else:
            # not an approved agency, all we do is mark as submitted
            self.status = 'submitted'
        self.save()

        # whether it is automailed or not, notify the followers (but not the owner)
        for profile in self.followed_by.all():
            profile.notify(self)

    def followup(self):
        """Send a follow up email for this request"""
        # pylint: disable=no-member
        from muckrock.foia.models.communication import FOIACommunication

        if self.date_estimate and date.today() < self.date_estimate:
            estimate = 'future'
        elif self.date_estimate:
            estimate = 'past'
        else:
            estimate = 'none'

        comm = FOIACommunication.objects.create(
            foia=self, from_who='MuckRock.com', to_who=self.get_to_who(),
            date=datetime.now(), response=False, full_html=False,
            communication=render_to_string('text/foia/followup.txt',
                {'request': self, 'estimate': estimate}))

        if not self.email and self.agency:
            self.email = self.agency.get_email()
            self.other_emails = self.agency.other_emails
            self.save()

        if self.email:
            self._send_email()
        else:
            self.status = 'submitted'
            self.save()
            comm.delivered = 'mail'
            comm.save()
            task.models.SnailMailTask.objects.create(category='f', communication=comm)

        # Do not self.update() here for now to avoid excessive emails
        self.update_dates()

    def _send_email(self):
        """Send an email of the request to its email address"""
        # pylint: disable=no-member
        # self.email should be set before calling this method

        from_addr = 'fax' if self.email.endswith('faxaway.com') else self.get_mail_id()
        law_name = self.jurisdiction.get_law_name()
        if self.tracking_id:
            subject = 'RE: %s Request #%s' % (law_name, self.tracking_id)
        elif self.communications.count() > 1:
            subject = 'RE: %s Request: %s' % (law_name, self.title)
        else:
            subject = '%s Request: %s' % (law_name, self.title)

        # get last comm to set delivered and raw_email
        comm = self.communications.reverse()[0]

        if from_addr == 'fax':
            subject = 'MR#%s-%s - %s' % (self.pk, comm.pk, subject)

        cc_addrs = self.get_other_emails()
        from_email = '%s@%s' % (from_addr, MAILGUN_SERVER_NAME)
        body = render_to_string('text/foia/request_email.txt', {'request': self})
        body = unidecode(body) if from_addr == 'fax' else body
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[self.email],
            bcc=cc_addrs + ['diagnostics@muckrock.com'],
            headers={
                'Cc': ','.join(cc_addrs),
                'X-Mailgun-Variables': '{"comm_id": %s}' % comm.pk
            }
        )
        if from_addr != 'fax':
            msg.attach_alternative(linebreaks(escape(body)), 'text/html')
        # atach all files from the latest communication
        for file_ in self.communications.reverse()[0].files.all():
            msg.attach(file_.name(), file_.ffile.read())
        msg.send(fail_silently=False)

        # update communication
        comm.set_raw_email(msg.message())
        comm.delivered = 'fax' if self.email.endswith('faxaway.com') else 'email'
        comm.save()

        # unblock incoming messages if we send one out
        self.block_incoming = False
        self.save()

    def update_dates(self):
        """Set the due date, follow up date and days until due attributes"""
        # pylint: disable=no-member

        cal = self.jurisdiction.get_calendar()

        # first submit
        if not self.date_submitted:
            self.date_submitted = date.today()
            days = self.jurisdiction.get_days()
            if days:
                self.date_due = cal.business_days_from(date.today(), days)

        # updated from mailgun without setting status or submitted
        if self.status in ['ack', 'processed']:

            # unpause the count down
            if self.days_until_due is not None:
                self.date_due = cal.business_days_from(date.today(), self.days_until_due)
                self.days_until_due = None

            self._update_followup_date()

        # if we are no longer waiting on the agency, do not follow up
        if self.status not in ['ack', 'processed'] and self.date_followup:
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
        # pylint: disable=no-member
        if self.date_estimate and date.today() < self.date_estimate:
            return 183
        if self.jurisdiction and self.jurisdiction.level == 'f':
            return 30
        else:
            return 15

    def update_tags(self, tags):
        """Update the requests tags"""
        tag_set = set()
        for tag in tags.split(','):
            tag = Tag.normalize(tag)
            if not tag:
                continue
            new_tag, _ = Tag.objects.get_or_create(name=tag)
            tag_set.add(new_tag)
        self.tags.set(*tag_set)

    def admin_actions(self, user):
        '''Provides action interfaces for admins'''
        kwargs = {
            'jurisdiction': self.jurisdiction.slug,
            'jidx': self.jurisdiction.pk,
            'idx': self.pk,
            'slug': self.slug
        }
        return [
            Action(
                test=user.is_staff,
                link=reverse('foia-admin-fix', kwargs=kwargs),
                title='Admin Fix',
                desc='Open the admin fix form',
                class_name='default'
            ),
        ]

    def user_actions(self, user):
        '''Provides action interfaces for users'''
        is_owner = self.user == user
        can_follow = user.is_authenticated() and not is_owner
        is_following = user.is_authenticated() and self.followed_by.filter(user=user)
        kwargs = {
            'jurisdiction': self.jurisdiction.slug,
            'jidx': self.jurisdiction.pk,
            'idx': self.pk,
            'slug': self.slug
        }
        return [
            Action(
                test=True,
                link=reverse('foia-clone', kwargs=kwargs),
                title='Clone',
                desc='Start a new request using this one as a base',
                class_name='primary'
            ),
            Action(
                test=can_follow,
                link=reverse('foia-follow', kwargs=kwargs),
                title=('Unfollow' if is_following else 'Follow'),
                class_name=('default' if is_following else 'primary')
            ),
            Action(
                test=True,
                title='Report',
                action='flag',
                desc=u'Something broken, buggy, or off?  Let us know and we’ll fix it',
                class_name='modal'
            ),
        ]

    def noncontextual_request_actions(self, user):
        '''Provides context-insensitive action interfaces for requests'''
        can_edit = self.editable_by(user) or user.is_staff
        can_embargo = not self.is_editable() and can_edit and user.profile.can_embargo()
        # pylint: disable=line-too-long
        can_permanently_embargo = can_embargo and self.is_embargo() and not self.is_permanently_embargoed()
        can_pay = can_edit and self.is_payable()
        kwargs = {
            'jurisdiction': self.jurisdiction.slug,
            'jidx': self.jurisdiction.pk,
            'idx': self.pk,
            'slug': self.slug
        }
        return [
            Action(
                test=can_permanently_embargo,
                link=reverse('foia-embargo-permanent', kwargs=kwargs),
                title='Permanently Embargo',
                desc='Permanently embargo this request',
                class_name='default'
            ),
            Action(
                test=can_embargo,
                link=reverse('foia-embargo', kwargs=kwargs),
                title=('Unembargo' if self.embargo else 'Embargo'),
                desc=('Make this request public' if self.embargo else 'Make this request private'),
                class_name='default'
            ),
            Action(
                test=can_pay,
                link=reverse('foia-pay', kwargs=kwargs),
                title='Pay',
                desc='Pay the fee for this request',
                class_name='success'
            ),
            Action(
                test=can_pay,
                link=reverse('foia-crowdfund', kwargs=kwargs),
                title='Crowdfund',
                desc='Ask the community to help pay the fee for this request',
                class_name='success'
            ),
        ]

    def contextual_request_actions(self, user):
        '''Provides context-sensitive action interfaces for requests'''
        can_edit = self.editable_by(user) or user.is_staff
        can_follow_up = can_edit and self.status != 'started'
        can_appeal = can_edit and self.is_appealable()
        return [
            Action(
                test=can_edit,
                title='Get Advice',
                action='question',
                desc=u'Get your questions answered by Muckrock’s community of FOIA experts',
                class_name='modal'
            ),
            Action(
                test=can_follow_up,
                title='Follow Up',
                action='follow_up',
                desc='Send a message directly to the agency',
                class_name='reply'
            ),
            Action(
                test=can_appeal,
                title='Appeal',
                action='appeal',
                desc=u'Appeal an agency’s decision',
                class_name='reply'
            ),
        ]

    def total_pages(self):
        """Get the total number of pages for this request"""
        # pylint: disable=no-member
        pages = self.files.aggregate(Sum('pages'))['pages__sum']
        if pages is None:
            return 0
        return pages

    def has_ack(self):
        """Has this request been acknowledged?"""
        # pylint: disable=no-member
        return self.communications.filter(response=True).exists()


    class Meta:
        # pylint: disable=too-few-public-methods
        ordering = ['title']
        verbose_name = 'FOIA Request'
        app_label = 'foia'


