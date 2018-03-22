# -*- coding: utf-8 -*-
"""
Models for the FOIA application
"""

# pylint: disable=too-many-lines

# Django
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import connection, models
from django.db.models import Sum
from django.template.defaultfilters import escape, linebreaks, slugify
from django.template.loader import get_template, render_to_string
from django.utils import timezone
from django.utils.encoding import smart_text

# Standard Library
import logging
import os.path
from datetime import date, timedelta
from hashlib import md5

# Third Party
from actstream.models import followers
from reversion import revisions as reversion
from taggit.managers import TaggableManager

# MuckRock
from muckrock import fields, task, utils
from muckrock.accounts.models import Notification
from muckrock.communication.models import EmailAddress, EmailCommunication
from muckrock.foia.querysets import FOIARequestQuerySet
from muckrock.tags.models import Tag, TaggedItemBase, parse_tags

logger = logging.getLogger(__name__)

STATUS = [
    ('started',
     'Draft'),  # XXX this status is removed (what to do for foia machine?)
    ('submitted', 'Processing'),
    ('ack', 'Awaiting Acknowledgement'),
    ('processed', 'Awaiting Response'),
    ('appealing', 'Awaiting Appeal'),
    ('fix', 'Fix Required'),
    ('payment', 'Payment Required'),
    ('lawsuit', 'In Litigation'),
    ('rejected', 'Rejected'),
    ('no_docs', 'No Responsive Documents'),
    ('done', 'Completed'),
    ('partial', 'Partially Completed'),
    ('abandoned', 'Withdrawn'),
]

END_STATUS = ['rejected', 'no_docs', 'done', 'partial', 'abandoned']


class FOIARequest(models.Model):
    """A Freedom of Information Act request"""
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes

    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS, db_index=True)
    agency = models.ForeignKey('agency.Agency')
    composer = models.ForeignKey('foia.FOIAComposer')
    # XXX rename this
    date_updated = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text='Date of latest communication',
    )
    # XXX rename this
    date_done = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name='Date response received',
    )
    date_due = models.DateField(blank=True, null=True, db_index=True)
    days_until_due = models.IntegerField(blank=True, null=True)
    date_followup = models.DateField(blank=True, null=True)
    date_estimate = models.DateField(
        blank=True, null=True, verbose_name='Estimated Date Completed'
    )
    date_processing = models.DateField(blank=True, null=True)

    embargo = models.BooleanField(default=False)
    permanent_embargo = models.BooleanField(default=False)
    date_embargo = models.DateField(blank=True, null=True)

    price = models.DecimalField(max_digits=14, decimal_places=2, default='0.00')
    # XXX do we want to reconsider how we do featured requests?
    featured = models.BooleanField(default=False)
    sidebar_html = models.TextField(blank=True)
    mail_id = models.CharField(blank=True, max_length=255, editable=False)

    portal = models.ForeignKey(
        'portal.Portal',
        related_name='foias',
        blank=True,
        null=True,
    )
    portal_password = models.CharField(
        max_length=20,
        blank=True,
    )
    email = models.ForeignKey(
        'communication.EmailAddress',
        related_name='foias',
        blank=True,
        null=True,
    )
    cc_emails = models.ManyToManyField(
        'communication.EmailAddress',
        related_name='cc_foias',
    )
    fax = models.ForeignKey(
        'communication.PhoneNumber',
        related_name='foias',
        blank=True,
        null=True,
    )
    address = models.ForeignKey(
        'communication.Address',
        related_name='foias',
        blank=True,
        null=True,
    )

    disable_autofollowups = models.BooleanField(default=False)
    # XXX missing proxy may work differently with a composer
    missing_proxy = models.BooleanField(
        default=False,
        help_text='This request requires a proxy to file, but no such '
        'proxy was avilable upon draft creation.'
    )
    block_incoming = models.BooleanField(
        default=False,
        help_text=(
            'Block emails incoming to this request from '
            'automatically being posted on the site'
        )
    )
    crowdfund = models.OneToOneField(
        'crowdfund.Crowdfund',
        related_name='foia',
        blank=True,
        null=True,
    )

    # XXX move permission fields to composer?
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
    access_key = models.CharField(blank=True, max_length=255)

    objects = FOIARequestQuerySet.as_manager()
    tags = TaggableManager(through=TaggedItemBase, blank=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
            'foia-detail',
            kwargs={
                'jurisdiction': self.jurisdiction.slug,
                'jidx': self.jurisdiction.pk,
                'slug': self.slug,
                'idx': self.pk,
            }
        )

    def save(self, *args, **kwargs):
        """Normalize fields before saving and set the embargo expiration if necessary"""
        self.slug = slugify(self.slug)
        self.title = self.title.strip()
        if self.embargo:
            if self.status in END_STATUS:
                default_date = date.today() + timedelta(30)
                existing_date = self.date_embargo
                self.date_embargo = default_date if not existing_date else existing_date
            else:
                self.date_embargo = None
        if self.status == 'submitted' and self.date_processing is None:
            self.date_processing = date.today()

        # add a reversion comment if possible
        if 'comment' in kwargs:
            comment = kwargs.pop('comment')
            if reversion.revision_context_manager.is_active():
                reversion.set_comment(comment)
        super(FOIARequest, self).save(*args, **kwargs)

    @property
    def user(self):
        """The request's user is its composer's user"""
        return self.composer.user

    @property
    def jurisdiction(self):
        """The request's jurisdiction is its agency's jurisdiction"""
        return self.agency.jurisdiction

    # XXX move this to rules
    def is_payable(self):
        """Can this request be payed for by the user?"""
        has_open_crowdfund = self.crowdfund and not self.crowdfund.expired()
        has_payment_status = self.status == 'payment'
        return has_payment_status and not has_open_crowdfund

    # XXX this seems like it should not be in the model, but view
    def get_stripe_amount(self):
        """Output a Stripe Checkout formatted price"""
        return int(self.price * 100)

    # XXX permision handling
    def is_public(self):
        """Is this document viewable to everyone"""
        return self.has_perm(AnonymousUser(), 'view')

    # Request Sharing and Permissions

    def has_perm(self, user, perm):
        """Short cut for checking a FOIA permission"""
        return user.has_perm('foia.%s_foiarequest' % perm, self)

    ## Creator

    def created_by(self, user):
        """Did this user create this request?"""
        return self.composer.user == user

    # XXX i dislike the how adding/removing/promoting/demoting is done
    ## Editors

    def has_editor(self, user):
        """Checks whether the given user is an editor."""
        return self.edit_collaborators.filter(pk=user.pk).exists()

    def add_editor(self, user):
        """Grants the user permission to edit this request."""
        if not self.has_viewer(user) and not self.created_by(user):
            self.edit_collaborators.add(user)
            logger.info('%s granted edit access to %s', user, self)

    def remove_editor(self, user):
        """Revokes the user's permission to edit this request."""
        self.edit_collaborators.remove(user)
        logger.info('%s revoked edit access from %s', user, self)

    def demote_editor(self, user):
        """Reduces the editor's access to that of a viewer."""
        self.remove_editor(user)
        self.add_viewer(user)

    ## Viewers

    def has_viewer(self, user):
        """Checks whether the given user is a viewer."""
        return self.read_collaborators.filter(pk=user.pk).exists()

    def add_viewer(self, user):
        """Grants the user permission to view this request."""
        if not self.has_editor(user) and not self.created_by(user):
            self.read_collaborators.add(user)
            logger.info('%s granted view access to %s', user, self)

    def remove_viewer(self, user):
        """Revokes the user's permission to view this request."""
        self.read_collaborators.remove(user)
        logger.info('%s revoked view access from %s', user, self)

    def promote_viewer(self, user):
        """Enhances the viewer's access to that of an editor."""
        self.remove_viewer(user)
        self.add_editor(user)

    ## Access key

    def generate_access_key(self):
        """Generates a random key for accessing the request when it is private."""
        key = utils.generate_key(24)
        self.access_key = key
        self.save()
        logger.info('New access key generated for %s', self)
        return key

    def get_files(self):
        """Get all files under this FOIA"""
        # XXX try to remove circular import
        from muckrock.foia.models import FOIAFile
        return FOIAFile.objects.filter(comm__foia=self)

    # XXX rename
    def first_request(self):
        """Return the first request text"""
        try:
            return self.communications.all()[0].communication
        except IndexError:
            return ''

    # XXX remove
    def last_comm(self):
        """Return the last communication"""
        return self.communications.last()

    def last_response(self):
        """Return the most recent response"""
        return self.communications.filter(response=True
                                          ).order_by('-date').first()

    def last_request(self):
        """Return the most recent request"""
        return self.communications.filter(response=False
                                          ).order_by('-date').first()

    def set_mail_id(self):
        """Set the mail id, which is the unique identifier for the auto mailer system"""
        # use raw sql here in order to avoid race conditions
        uid = int(
            md5(self.title.encode('utf8') + timezone.now().isoformat())
            .hexdigest(), 16
        ) % 10 ** 8
        mail_id = '%s-%08d' % (self.pk, uid)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE foia_foiarequest "
            "SET mail_id = CASE WHEN mail_id='' THEN %s ELSE mail_id END "
            "WHERE id = %s",
            [mail_id, self.pk]
        )
        # set object's mail id to what is in the database
        self.mail_id = FOIARequest.objects.get(pk=self.pk).mail_id

    # XXX merge with get_request email?
    def get_mail_id(self):
        """Get the mail id - generate it if it doesn't exist"""
        if not self.mail_id:
            self.set_mail_id()
        return self.mail_id

    def get_request_email(self):
        """Get the request's unique email address"""
        return '%s@%s' % (self.get_mail_id(), settings.MAILGUN_SERVER_NAME)

    def get_other_emails(self):
        """Get the other emails for this request as a comma seperated string"""
        return ', '.join(unicode(e) for e in self.cc_emails.all())

    def get_to_user(self):
        """Who communications are to"""
        return self.agency.get_user()

    def get_saved(self):
        # XXX ehh
        """Get the old model that is saved in the db"""
        try:
            return FOIARequest.objects.get(pk=self.pk)
        except FOIARequest.DoesNotExist:
            return None

    def latest_response(self):
        """How many days since the last response"""
        response = self.last_response()
        if response:
            return (date.today() - response.date.date()).days

    def processing_length(self):
        """How many days since the request was set as processing"""
        days_since = 0
        if self.date_processing:
            days_since = (date.today() - self.date_processing).days
        return days_since

    def update(self, anchor=None):
        """Various actions whenever the request has been updated"""
        # pylint: disable=unused-argument
        # Do something with anchor
        # XXX
        self.update_dates()

    def notify(self, action):
        """
        Notify the owner of the request.
        Notify followers if the request is not under embargo.
        Mark any existing notifications with the same message as read,
        to avoid notifying users with duplicated information.
        """
        identical_notifications = (
            Notification.objects.for_object(self).get_unread().filter(
                action__actor_object_id=action.actor_object_id,
                action__verb=action.verb
            )
        )
        for notification in identical_notifications:
            notification.mark_read()
        utils.notify(self.composer.user, action)
        if self.is_public():
            utils.notify(followers(self), action)

    # XXX split up sending responsiblity across composer and comm?
    def submit(self, appeal=False, **kwargs):
        """
        The request has been submitted.
        Notify admin and try to auto submit.
        There is functionally no difference between appeals and other submissions
        besides the receiving agency.
        The only difference between a thanks andother submissions is that we do
        not set the request status, unless the request requires a proxy.
        """
        if not self.agency:
            # this should not happen
            raise ValueError('Trying to submit a request without an agency.')

        if appeal and self.agency.appeal_agency:
            agency = self.agency.appeal_agency
        else:
            agency = self.agency

        if kwargs.get('contact_info'):
            needs_review = self.update_address_from_info(
                agency,
                appeal,
                kwargs.get('contact_info'),
            )
        else:
            needs_review = False
            self.update_address_from_agency(agency, appeal, kwargs.get('clear'))

        # if agency isnt approved, do not email or snail mail
        # it will be handled after agency is approved
        approved_agency = agency.status == 'approved'

        if self.missing_proxy:
            self._flag_proxy_resubmit()
            self.save()
        elif not approved_agency:
            # not an approved agency, all we do is mark as submitted
            self.status = 'submitted'
            self.date_processing = date.today()
            self.save()
        elif needs_review:
            # if the user submitted new contact information, leave processing
            # and create a flag
            self.status = 'submitted'
            self.date_processing = date.today()
            self.save()
        else:
            self.update_dates()
            self.save()
            self._send_msg(appeal=appeal, **kwargs)

    def update_address_from_info(self, agency, appeal, contact_info):
        """Update the contact information manually"""

        # first clear all current contact information
        self.portal = None
        self.email = None
        self.cc_emails.clear()
        self.fax = None
        self.address = None

        if appeal:
            request_type = 'appeal'
        else:
            request_type = 'primary'
        # always set the address as a fallback option
        self.address = agency.get_addresses(request_type).first()

        if contact_info['via'] == 'portal':
            self.portal = agency.portal
        elif contact_info['via'] == 'email' and contact_info['email']:
            self.email = contact_info['email']
        elif contact_info['via'] == 'email':
            self.email = contact_info['other_email']
            # Flag for review
            task.models.FlaggedTask.objects.create(
                foia=self,
                text='This request was filed with a user supplied email '
                'address: {}.  Please check that this is an appropriate email '
                'address before sending this request'.format(self.email),
            )
            return True
        elif contact_info['via'] == 'fax' and contact_info['fax']:
            self.fax = contact_info['fax']
        elif contact_info['via'] == 'fax':
            self.fax = contact_info['other_fax']
            # Flag for review
            task.models.FlaggedTask.objects.create(
                foia=self,
                text='This request was filed with a user supplied fax '
                'number: {}.  Please check that this is an appropriate fax '
                'number before sending this request'.format(self.fax),
            )
            return True

        # Does not need review
        return False

    def update_address_from_agency(self, agency, appeal, clear):
        """Update the current address for the request"""
        # if this is an appeal, clear the current addresses and get them
        # from the appeal agency
        if appeal or clear:
            self.portal = None
            self.email = None
            self.cc_emails.clear()
            self.fax = None
            self.address = None
        if appeal:
            request_type = 'appeal'
        else:
            request_type = 'primary'

        # set addresses if none have been set yet or if they have been cleared
        if not self.portal and not self.email and not self.fax and not self.address:
            if not appeal:
                self.portal = agency.portal
            self.email = agency.get_emails(request_type, 'to').first()
            self.cc_emails.set(agency.get_emails(request_type, 'cc'))
            self.fax = agency.get_faxes(request_type).first()
            self.address = agency.get_addresses(request_type).first()
        self.save(comment='update address from agency')

    def update_address(self, via, email, fax, other_emails=None):
        """Update the current address"""
        # lower priority address types clear out higher priority types to make
        # them the new default, except for snail mail, as we may want to snail
        # mail a single communication without making that the new default
        if via == 'portal':
            self.portal = self.agency.portal
        elif via == 'email':
            self.portal = None
            self.email = email
            if other_emails is not None:
                self.cc_emails.set(other_emails)
        elif via == 'fax':
            self.portal = None
            self.email = None
            self.cc_emails.clear()
            self.fax = fax
        elif via == 'snail':
            self.address = self.agency.get_addresses().first()
        self.save(comment='update address')

    def _flag_proxy_resubmit(self):
        """Flag this request to be re-submitted with a proxy"""
        self.status = 'submitted'
        self.date_processing = date.today()
        task.models.FlaggedTask.objects.create(
            foia=self,
            text='This request was filed for an agency requiring a '
            'proxy, but no proxy was available.  Please add a suitable '
            'proxy for the state and refile it with a note that the '
            'request is being filed by a state citizen. Make sure the '
            'new request is associated with the original user\'s '
            'account. To add someone as a proxy, change their user type '
            'to "Proxy" and make sure they properly have their state '
            'set on the backend.  This message should only appear when '
            'a suitable proxy does not exist.'
        )

    def process_attachments(self, user):
        """Attach all outbound attachments to the last communication"""
        attachments = self.pending_attachments.filter(
            user=user,
            sent=False,
        )
        comm = self.last_comm()
        access = 'private' if self.embargo else 'public'
        for attachment in attachments:
            file_ = comm.files.create(
                title=os.path.basename(attachment.ffile.name),
                date=comm.date,
                source=user.get_full_name(),
                access=access,
            )
            file_.ffile.name = attachment.ffile.name
            file_.save()
        attachments.update(sent=True)

    def followup(self, switch=False):
        """Send an automatic follow up email for this request"""
        if self.date_estimate and date.today() < self.date_estimate:
            estimate = 'future'
        elif self.date_estimate:
            estimate = 'past'
        else:
            estimate = 'none'

        text = render_to_string(
            'text/foia/followup.txt', {
                'request': self,
                'estimate': estimate
            }
        )

        user = User.objects.get(username='MuckrockStaff')
        return self.create_out_communication(
            from_user=user,
            text=text,
            user=user,
            autogenerated=True,
            followup=True,
            switch=switch,
        )

    def appeal(self, appeal_message, user):
        """Send an appeal to the agency or its appeal agency."""
        return self.create_out_communication(
            from_user=user,
            text=appeal_message,
            user=user,
            appeal=True,
            # we include the latest pdf here under the assumption
            # it is the rejection letter
            include_latest_pdf=True,
        )

    def pay(self, user, amount):
        """
        Users can make payments for request fees.
        Upon payment, we create a snail mail task and we set the request to a processing status.
        Payments are always snail mail, because we need to mail the check to the agency.
        Since collaborators may make payments, we do not assume the user is the request creator.
        Returns the communication that was generated.
        """
        # We create the payment communication and a snail mail task for it.
        payable_to = self.agency.payable_to if self.agency else None
        text = render_to_string(
            'message/communication/payment.txt', {
                'amount': amount,
                'payable_to': payable_to,
            }
        )

        comm = self.create_out_communication(
            from_user=user,
            text=text,
            user=user,
            payment=True,
            snail=True,
            amount=amount,
            # we include the latest pdf here under the assumption
            # it is the invoice
            include_latest_pdf=True,
        )

        # We perform some logging and activity generation
        logger.info(
            '%s has paid %0.2f for request %s', user.username, amount,
            self.title
        )
        utils.new_action(user, 'paid fees', target=self)
        # We return the communication we generated, in case the caller wants to do anything with it
        return comm

    def _send_msg(self, **kwargs):
        """Send a message for this request"""
        # self.email / self.fax / self.address should be set
        # before calling this method

        comm = kwargs.pop(
            'comm',
            self.communications.last(),
        )
        subject = comm.subject or self.default_subject()
        subject = subject[:255]
        comm.subject = subject

        # attach the pdf form if one exists and this is the initial request
        if self.agency.form and self.communications.count() == 1:
            self.agency.form.fill(comm)

        # preferred order of communication methods
        if self.portal and self.portal.status == 'good' and not kwargs.get(
            'snail'
        ):
            self._send_portal(comm, **kwargs)
        elif self.email and self.email.status == 'good' and not kwargs.get(
            'snail'
        ):
            self._send_email(comm, **kwargs)
        elif self.fax and self.fax.status == 'good' and not kwargs.get('snail'):
            self._send_fax(comm, **kwargs)
        else:
            self._send_snail_mail(comm, **kwargs)

        comm.save()

        # unblock incoming messages if we send one out
        self.block_incoming = False
        self.save()

    def _send_portal(self, comm, **kwargs):
        """Send the message via portal"""
        self.portal.send_msg(comm, **kwargs)

    def _send_email(self, comm, **kwargs):
        """Send the message as an email"""

        from_email, _ = EmailAddress.objects.get_or_create(
            email=self.get_request_email(),
        )

        body = self.render_msg_body(
            comm=comm,
            reply_link=True,
            switch=kwargs.get('switch'),
            appeal=kwargs.get('appeal')
        )

        self.status = self._sent_status(
            kwargs.get('appeal'),
            kwargs.get('thanks'),
        )

        email_comm = EmailCommunication.objects.create(
            communication=comm,
            sent_datetime=timezone.now(),
            from_email=from_email,
        )
        email_comm.to_emails.add(self.email)
        email_comm.cc_emails.set(self.cc_emails.all())
        msg = EmailMultiAlternatives(
            subject=comm.subject,
            body=body,
            from_email=str(from_email),
            to=[str(self.email)],
            cc=[str(e) for e in self.cc_emails.all() if e.status == 'good'],
            bcc=['diagnostics@muckrock.com'],
            headers={
                'X-Mailgun-Variables': {
                    'email_id': email_comm.pk
                },
            }
        )
        msg.attach_alternative(linebreaks(escape(body)), 'text/html')
        # atach all files from the latest communication
        comm.attach_files_to_email(msg)

        msg.send(fail_silently=False)

        email_comm.set_raw_email(msg.message())

    def _send_fax(self, comm, **kwargs):
        """Send the message as a fax"""
        from muckrock.foia.tasks import send_fax

        switch = (
            kwargs.get('switch')
            or ((self.email and self.email.status == 'error') and
                (self.last_request().sent_to() == self.email))
        )

        body = self.render_msg_body(
            comm=comm, switch=switch, appeal=kwargs.get('appeal')
        )

        self.status = self._sent_status(
            kwargs.get('appeal'),
            kwargs.get('thanks'),
        )

        error_count = kwargs.get('fax_error_count', 0)
        if error_count > 0:
            # after the first error, wait for 3 hours,
            # then double the time for every additional error
            countdown = 60 * 60 * 3 * (2 ** (error_count - 1))
        else:
            countdown = 0

        send_fax.apply_async(
            args=[comm.pk, comm.subject, body, error_count],
            countdown=countdown,
        )

    def _send_snail_mail(self, comm, **kwargs):
        """Send the message as a snail mail"""
        category, extra = self.process_manual_send(**kwargs)

        switch = bool(
            kwargs.get('switch', False)
            or ((self.email and self.email.status == 'error') and
                (self.last_request().sent_to() == self.email))
            or ((self.fax and self.fax.status == 'error') and
                (self.last_request().sent_to() == self.fax))
        )

        task.models.SnailMailTask.objects.create(
            category=category,
            communication=comm,
            user=comm.from_user,
            switch=switch,
            **extra
        )

    def process_manual_send(self, **kwargs):
        """Select a category and set status for manually processed
        sends - snail mails or manual portal tasks"""
        if not kwargs.get('thanks'):
            self.status = 'submitted'
            self.date_processing = date.today()
        if kwargs.get('appeal'):
            category = 'a'
        elif kwargs.get('payment'):
            category = 'p'
        elif kwargs.get('followup'):
            category = 'f'
        elif self.communications.count() == 1:
            category = 'n'
        else:
            category = 'u'
        if 'amount' in kwargs:
            extra = {'amount': kwargs['amount']}
        else:
            extra = {}
        return (category, extra)

    def render_msg_body(
        self, comm, reply_link=False, switch=False, appeal=False
    ):
        """Render the message body for outgoing messages"""
        context = {
            'request': self,
            'switch': switch,
            'msg_comms': self.get_msg_comms(comm),
        }
        if self.address:
            if appeal and self.agency and self.agency.appeal_agency:
                agency = self.agency.appeal_agency
            else:
                agency = self.agency
            context['address'] = self.address.format(agency, appeal=appeal)
        if reply_link:
            context['reply_link'] = self.get_agency_reply_link(self.email.email)
        if switch:
            first_request = self.communications.all()[0]
            context['original'] = {
                'method': first_request.get_delivered(),
                'addr': first_request.sent_to(),
            }
            last_response = self.last_response()
            if last_response:
                method, addr = last_response.get_delivered_and_from()
                context['last_resp'] = {
                    'date': last_response.date,
                    'method': method,
                    'addr': addr,
                }

        return render_to_string(
            'text/foia/request_msg.txt',
            context,
        )

    def _sent_status(self, appeal, thanks):
        """After sending out the message, set the correct new status"""
        if thanks:
            return self.status
        elif appeal:
            return 'appealing'
        elif self.has_ack():
            return 'processed'
        else:
            return 'ack'

    # XXX this is a mess
    def update_dates(self):
        """Set the due date, follow up date and days until due attributes"""
        cal = self.jurisdiction.get_calendar()
        # first submit
        if not self.composer.datetime_submitted:
            self.composer.datetime_submitted = timezone.now()
            self.composer.save()
            days = self.jurisdiction.days
            if days:
                self.date_due = cal.business_days_from(date.today(), days)
        # updated from mailgun without setting status or submitted
        if self.status in ['ack', 'processed']:
            # unpause the count down
            if self.days_until_due is not None:
                self.date_due = cal.business_days_from(
                    date.today(), self.days_until_due
                )
                self.days_until_due = None
            self._update_followup_date()
        # if we are no longer waiting on the agency, do not follow up
        if self.status not in ['ack', 'processed'] and self.date_followup:
            self.date_followup = None
        # if we need to respond, pause the count down until we do
        if self.status in ['fix', 'payment'] and self.date_due:
            last_datetime = self.last_comm().date
            if not last_datetime:
                last_datetime = timezone.now()
            self.days_until_due = cal.business_days_between(
                last_datetime.date(), self.date_due
            )
            self.date_due = None
        self.save()

    def _update_followup_date(self):
        """Update the follow up date"""
        try:
            new_date = self.last_comm().date.date() + timedelta(
                self._followup_days()
            )
            if self.date_due and self.date_due > new_date:
                new_date = self.date_due

            if not self.date_followup or self.date_followup < new_date:
                self.date_followup = new_date

        except IndexError:
            # This request has no communications at the moment, cannot asign a follow up date
            pass

    def _followup_days(self):
        """How many days do we wait until we follow up?"""
        if self.status == 'ack' and self.jurisdiction:
            # if we have not at least been acknowledged yet, set the days
            # to the period required by law
            jurisdiction_days = self.jurisdiction.days
            if jurisdiction_days is not None:
                return jurisdiction_days
        if self.date_estimate and date.today() < self.date_estimate:
            # return the days until the estimated date
            date_difference = self.date_estimate - date.today()
            return date_difference.days
        if self.portal is not None:
            # if it is using a portal, give them extra time
            return 90
        if self.jurisdiction and self.jurisdiction.level == 'f':
            return 30
        else:
            return 15

    # XXX somewhere else?
    def get_agency_reply_link(self, email):
        """Get the link for the agency user to log in"""
        agency = self.agency
        agency_user_profile = agency.get_user().profile
        return agency_user_profile.wrap_url(
            reverse(
                'acct-agency-redirect-login',
                kwargs={
                    'agency_slug': agency.slug,
                    'agency_idx': agency.pk,
                    'foia_slug': self.slug,
                    'foia_idx': self.pk,
                },
            ),
            email=email,
        )

    # XXX necessary?
    def update_tags(self, tags):
        """Update the requests tags"""
        tag_set = set()
        for tag in parse_tags(tags):
            new_tag, _ = Tag.objects.get_or_create(name=tag)
            tag_set.add(new_tag)
        self.tags.set(*tag_set)

    # XXX should not be in models
    def user_actions(self, user):
        """Provides action interfaces for users"""
        from muckrock.foia.forms import FOIAFlagForm, FOIAContactUserForm
        is_owner = self.created_by(user)
        is_agency_user = (
            user.is_authenticated() and user.profile.acct_type == 'agency'
        )
        can_follow = (
            user.is_authenticated() and not is_owner and not is_agency_user
        )
        is_following = user.is_authenticated() and user in followers(self)
        is_admin = user.is_staff
        kwargs = {
            'jurisdiction': self.jurisdiction.slug,
            'jidx': self.jurisdiction.pk,
            'idx': self.pk,
            'slug': self.slug
        }
        return [
            {
                'test': not is_agency_user,
                'link': reverse('foia-clone', kwargs=kwargs),
                'title': 'Clone',
                'desc': 'Start a new request using this one as a base',
                'class_name': 'primary',
            },
            {
                'test': can_follow,
                'link': reverse('foia-follow', kwargs=kwargs),
                'title': ('Unfollow' if is_following else 'Follow'),
                'class_name': ('default' if is_following else 'primary'),
            },
            {
                'test': self.has_perm(user, 'zip_download'),
                'link': '?zip_download=1',
                'title': 'Download as Zip',
                'desc':
                    u'Download all communications and '
                    u'files as a zip archive',
                'class_name': 'primary',
            },
            {
                'test': self.has_perm(user, 'flag'),
                'title': 'Get Help',
                'action': 'flag',
                'desc':
                    u'Something broken, buggy, or off?  '
                    u'Let us know and we\'ll fix it',
                'class_name': 'failure',
                'modal': True,
                'form': FOIAFlagForm(),
            },
            {
                'test': is_admin,
                'title': 'Contact User',
                'action': 'contact_user',
                'desc': u'Send this request\'s owner an email',
                'modal': True,
                'form': FOIAContactUserForm(),
            },
        ]

    # XXX this is only ever used to check for > 0...
    def total_pages(self):
        """Get the total number of pages for this request"""
        pages = self.get_files().aggregate(Sum('pages'))['pages__sum']
        if pages is None:
            return 0
        return pages

    def has_ack(self):
        """Has this request been acknowledged?"""
        return self.communications.filter(response=True).exists()

    def proxy_reject(self):
        """Mark this request as being rejected due to a proxy being required"""
        from muckrock.task.models import FlaggedTask
        # mark the agency as requiring a proxy going forward
        self.agency.requires_proxy = True
        self.agency.save()
        # mark to re-file with a proxy
        FlaggedTask.objects.create(
            foia=self,
            text='This request was rejected as requiring a proxy; please refile'
            ' it with one of our volunteers names and a note that the request is'
            ' being filed by a state citizen. Make sure the new request is'
            ' associated with the original user\'s account. To add someone as'
            ' a proxy, change their user type to "Proxy" and make sure they'
            ' properly have their state set on the backend. This message should'
            ' only appear the first time an agency rejects a request for being'
            ' from an out-of-state resident.'
        )
        self.notes.create(
            author=User.objects.get(username='MuckrockStaff'),
            note='The request has been rejected with the agency stating that '
            'you must be a resident of the state. MuckRock is working with our '
            'in-state volunteers to refile this request, and it should appear '
            'in your account within a few days.',
        )

    def default_subject(self):
        """Make a subject line for a communication for this request"""
        law_name = self.jurisdiction.get_law_name()
        tracking_id = self.current_tracking_id()
        if tracking_id:
            return 'RE: %s Request #%s' % (law_name, tracking_id)
        elif self.communications.count() > 1:
            return 'RE: %s Request: %s' % (law_name, self.title)
        else:
            return '%s Request: %s' % (law_name, self.title)

    def get_msg_comms(self, comm):
        """Get the communications to be displayed for outgoing messages"""
        msg_comms = []
        # filtering in python here to use pre-cached communications
        comms = list(c for c in self.communications.all() if not c.hidden)
        # if the comm we are sending is not the last one (for a resend) tack
        # it on to the end
        if comms[-1] != comm:
            comms.append(comm)
        # if theirs only one communication, do not double include it
        if len(comms) == 1:
            return comms
        # always show the latest message
        msg_comms.append(comms[-1])
        # get up to the 5 latest non-autogenerated requests
        # (excluding the latest and the orginal, which we always include)
        msg_comms.extend([c for c in comms[1:-1][::-1]
                          if not c.autogenerated][:5])
        # always include the original
        msg_comms.append(comms[0])
        return msg_comms

    def create_out_communication(self, from_user, text, user, **kwargs):
        """Create an outgoing communication"""
        pdfs = []
        if kwargs.get('include_latest_pdf'):
            last_comm = self.communications.filter(response=True).last()
            if last_comm:
                pdfs = last_comm.files.filter(ffile__endswith='.pdf')
        comm = self.communications.create(
            from_user=from_user,
            to_user=self.get_to_user(),
            date=timezone.now(),
            response=False,
            communication=text,
            thanks=kwargs.get('thanks', False),
            subject=kwargs.get('subject', ''),
            autogenerated=kwargs.get('autogenerated', False),
        )
        self.communications.update()
        for pdf in pdfs:
            pdf.clone(comm)
        self.process_attachments(user)
        self.submit(
            appeal=kwargs.get('appeal', False),
            snail=kwargs.get('snail', False),
            thanks=kwargs.get('thanks', False),
            followup=kwargs.get('followup', False),
            payment=kwargs.get('payment', False),
            amount=kwargs.get('amount', 0),
            switch=kwargs.get('switch', False),
            contact_info=kwargs.get('contact_info'),
        )
        return comm

    def create_initial_communication(self, from_user, proxy):
        """Create the initial request communication"""
        template = get_template('text/foia/request.txt')
        context = {
            'document_request': smart_text(self.composer.requested_docs),
            'jurisdiction': self.jurisdiction,
            'user_name': from_user.get_full_name(),
            'proxy': proxy,
        }
        text = template.render(context).strip()
        comm = self.communications.create(
            from_user=from_user,
            to_user=self.get_to_user(),
            date=timezone.now(),
            response=False,
            communication=text,
        )
        return comm

    def current_tracking_id(self):
        """Get the current tracking ID"""
        # pylint: disable=access-member-before-definition
        # pylint: disable=attribute-defined-outside-init
        if hasattr(self, '_tracking_id'):
            return self._tracking_id
        tracking_ids = self.tracking_ids.all()
        if tracking_ids:
            self._tracking_id = tracking_ids[0].tracking_id
        else:
            self._tracking_id = ''
        return self._tracking_id

    def add_tracking_id(self, tracking_id, reason=None):
        """Add a new tracking ID"""
        # pylint: disable=attribute-defined-outside-init
        if tracking_id == self.current_tracking_id():
            return
        if reason is None:
            if self.tracking_ids.exists():
                reason = 'other'
            else:
                reason = 'initial'
        self.tracking_ids.create(
            tracking_id=tracking_id,
            reason=reason,
        )
        self._tracking_id = tracking_id

    def add_contact_info_note(self, user, contact_info):
        """Add a note that contact info has been overridden"""
        via = contact_info.get('via', '')
        addr = contact_info.get(via, '')
        self.notes.create(
            author=user,
            note='Contact information overridden:\n\n{}\n\n{}'.format(
                via, addr
            )
        )

    class Meta:
        ordering = ['title']
        verbose_name = 'FOIA Request'
        app_label = 'foia'
        permissions = (
            ('view_foiarequest', 'Can view this request'),
            ('embargo_foiarequest', 'Can embargo request to make it private'),
            ('embargo_perm_foiarequest', 'Can embargo a request permananently'),
            (
                'crowdfund_foiarequest',
                'Can start a crowdfund campaign for the request'
            ),
            ('appeal_foiarequest', 'Can appeal the requests decision'),
            ('thank_foiarequest', 'Can thank the FOI officer for their help'),
            ('flag_foiarequest', 'Can flag the request for staff attention'),
            ('followup_foiarequest', 'Can send a manual follow up'),
            ('agency_reply_foiarequest', 'Can send a direct reply'),
            ('upload_attachment_foiarequest', 'Can upload an attachment'),
            ('export_csv', 'Can export a CSV of search results'),
            (
                'zip_download',
                'Can download a zip file of all communications and files'
            ),
        )


class TrackingNumber(models.Model):
    """A tracking number for a FOIA Request"""
    foia = models.ForeignKey(
        FOIARequest,
        on_delete=models.CASCADE,
        related_name='tracking_ids',
    )
    tracking_id = models.CharField(
        max_length=255,
        verbose_name='Tracking Number',
    )
    datetime = models.DateTimeField(default=timezone.now)
    reason = models.CharField(
        max_length=7,
        choices=(
            ('initial', 'Initial'),
            ('appeal', 'Appeal'),
            ('agency', 'New agency'),
            ('other', 'Other'),
        ),
    )

    def __unicode__(self):
        return self.tracking_id

    class Meta:
        ordering = ['-datetime']
