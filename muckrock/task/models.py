"""
Models for the Task application
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Prefetch

from datetime import datetime
import logging
from itertools import groupby

from muckrock.accounts.models import Notification
from muckrock.communication.models import (
        EmailCommunication,
        EmailError,
        EmailOpen,
        FaxCommunication,
        FaxError,
        )
from muckrock.foia.models import (
    FOIACommunication,
    FOIAFile,
    FOIANote,
    FOIARequest,
    STATUS,
)
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.message.email import TemplateEmail
from muckrock.message.tasks import support
from muckrock.utils import generate_status_action

# pylint: disable=missing-docstring

SNAIL_MAIL_CATEGORIES = [
    ('a', 'Appeal'),
    ('n', 'New'),
    ('u', 'Update'),
    ('f', 'Followup'),
    ('p', 'Payment'),
]

class TaskQuerySet(models.QuerySet):
    """Object manager for all tasks"""
    def get_unresolved(self):
        """Get all unresolved tasks"""
        return self.filter(resolved=False)

    def get_resolved(self):
        """Get all resolved tasks"""
        return self.filter(resolved=True)

    def filter_by_foia(self, foia, user):
        """
        Get tasks that relate to the provided FOIA request.
        If user is staff, get all tasks.
        If user is advanced, get response tasks.
        For all users, get new agency task.
        """
        # pylint:disable=no-self-use
        tasks = []
        # infer foia from communication
        communication_task_types = []
        if user.is_staff:
            communication_task_types.append(ResponseTask)
            communication_task_types.append(SnailMailTask)
        for task_type in communication_task_types:
            tasks += list(task_type.objects
                    .filter(communication__foia=foia)
                    .select_related('communication__foia', 'resolved_by')
                    .prefetch_related(
                        Prefetch('communication__files',
                            queryset=FOIAFile.objects.select_related('foia__jurisdiction')),
                        Prefetch('communication__foia__communications',
                            queryset=FOIACommunication.objects
                                .order_by('-date')
                                .prefetch_related(
                                    'files',
                                    'emails',
                                    'faxes',
                                    'mails',
                                    'web_comms',
                                    ),
                            to_attr='reverse_communications'),
                        'communication__foia__communications__files',
                        'communication__emails',
                        'communication__faxes',
                        'communication__mails',
                        'communication__web_comms',
                        )
                    )
        # these tasks have a direct foia attribute
        foia_task_types = [FlaggedTask, StatusChangeTask]
        if user.is_staff:
            for task_type in foia_task_types:
                tasks += list(task_type.objects
                        .filter(foia=foia)
                        .select_related('foia__jurisdiction', 'resolved_by'))
        # try matching foia agency with task agency
        if foia.agency:
            tasks += list(NewAgencyTask.objects
                    .filter(agency=foia.agency)
                    .preload_list()
                    .select_related('resolved_by'))
        return tasks


class OrphanTaskQuerySet(models.QuerySet):
    """Object manager for orphan tasks"""
    def get_from_domain(self, domain):
        """Get all orphan tasks from a specific domain"""
        return self.filter(communication__emails__from_email__email__icontains=domain)


class NewAgencyTaskQuerySet(models.QuerySet):
    """Object manager for new agency tasks"""
    def preload_list(self):
        """Preload relations for list display"""
        from muckrock.agency.models import Agency
        return (self.select_related('agency__jurisdiction')
                .prefetch_related(
                    Prefetch('agency__foiarequest_set',
                        queryset=FOIARequest.objects.select_related('jurisdiction')),
                    Prefetch('agency__jurisdiction__agencies',
                        queryset=Agency.objects
                        .filter(status='approved')
                        .order_by('name'),
                        to_attr='other_agencies')))


class Task(models.Model):
    """A base task model for fields common to all tasks"""
    date_created = models.DateTimeField(auto_now_add=True)
    date_done = models.DateTimeField(blank=True, null=True)
    resolved = models.BooleanField(default=False, db_index=True)
    assigned = models.ForeignKey(User, blank=True, null=True, related_name="assigned_tasks")
    resolved_by = models.ForeignKey(User, blank=True, null=True, related_name="resolved_tasks")

    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ['date_created']

    def __unicode__(self):
        # pylint:disable=no-self-use
        return u'Task'

    def resolve(self, user=None):
        """Resolve the task"""
        self.resolved = True
        self.resolved_by = user
        self.date_done = datetime.now()
        self.save()
        logging.info('User %s resolved task %s', user, self.pk)


class GenericTask(Task):
    """A generic task"""
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)

    def __unicode__(self):
        return u'Generic Task'


class OrphanTask(Task):
    """A communication that needs to be approved before showing it on the site"""
    type = 'OrphanTask'
    reasons = (('bs', 'Bad Sender'),
               ('ib', 'Incoming Blocked'),
               ('ia', 'Invalid Address'))
    reason = models.CharField(max_length=2, choices=reasons)
    communication = models.ForeignKey('foia.FOIACommunication')
    address = models.CharField(max_length=255)

    objects = OrphanTaskQuerySet.as_manager()
    template_name = 'task/orphan.html'

    def __unicode__(self):
        return u'Orphan Task'

    def get_absolute_url(self):
        return reverse('orphan-task', kwargs={'pk': self.pk})

    def move(self, foia_pks):
        """Moves the comm and creates a ResponseTask for it"""
        moved_comms = self.communication.move(foia_pks)
        for moved_comm in moved_comms:
            ResponseTask.objects.create(
                communication=moved_comm,
                created_from_orphan=True
            )
            moved_comm.make_sender_primary_contact()

    def reject(self, blacklist=False):
        """If blacklist is true, should blacklist the sender's domain."""
        if blacklist:
            self.blacklist()

    def get_sender_domain(self):
        """Gets the domain of the sender's email address."""
        try:
            return self.communication.emails.all()[0].from_email.domain
        except IndexError:
            return None

    def blacklist(self):
        """Adds the communication's sender's domain to the email blacklist."""
        domain = self.get_sender_domain()
        if domain is None:
            return
        try:
            blacklist, _ = BlacklistDomain.objects.get_or_create(domain=domain)
        except BlacklistDomain.MultipleObjectsReturned:
            blacklist = BlacklistDomain.objects.filter(domain=domain).first()
        blacklist.resolve_matches()


class SnailMailTask(Task):
    """A communication that needs to be snail mailed"""
    type = 'SnailMailTask'
    category = models.CharField(max_length=1, choices=SNAIL_MAIL_CATEGORIES)
    communication = models.ForeignKey('foia.FOIACommunication')
    user = models.ForeignKey(User, blank=True, null=True)
    amount = models.DecimalField(default=0.00, max_digits=8, decimal_places=2)

    def __unicode__(self):
        return u'Snail Mail Task'

    def get_absolute_url(self):
        return reverse('snail-mail-task', kwargs={'pk': self.pk})

    def set_status(self, status):
        """Set the status of the comm and FOIA affiliated with this task"""
        comm = self.communication
        comm.status = status
        comm.save()
        comm.foia.status = status
        comm.foia.save(comment='snail mail task')
        comm.foia.update()

    def update_text(self, new_text):
        """Sets the body text of the communication"""
        comm = self.communication
        comm.communication = new_text
        comm.save()

    def record_check(self, number, user):
        """Records the check to a note on the request"""
        foia = self.communication.foia
        text = "A check (#%(number)d) of $%(amount).2f was mailed to the agency." % {
            'number': number,
            'amount': self.amount
        }
        note = FOIANote.objects.create(foia=foia, note=text, author=user)
        return note


class RejectedEmailTask(Task):
    """
    Deprecated: Keeping this model around to not lose historical data

    A FOIA request has had an outgoing email rejected"""
    type = 'RejectedEmailTask'
    categories = (('b', 'Bounced'), ('d', 'Dropped'))
    category = models.CharField(max_length=1, choices=categories)
    foia = models.ForeignKey('foia.FOIARequest', blank=True, null=True)
    email = models.EmailField(blank=True)
    error = models.TextField(blank=True)

    def __unicode__(self):
        return u'Rejected Email Task'

    def get_absolute_url(self):
        return reverse('rejected-email-task', kwargs={'pk': self.pk})


class StaleAgencyTask(Task):
    """An agency has gone stale"""
    type = 'StaleAgencyTask'
    agency = models.ForeignKey('agency.Agency')

    def __unicode__(self):
        return u'Stale Agency Task'

    def get_absolute_url(self):
        return reverse('stale-agency-task', kwargs={'pk': self.pk})

    def resolve(self, user=None):
        """Unmark the agency as stale when resolving"""
        self.agency.unmark_stale()
        super(StaleAgencyTask, self).resolve(user)

    def stale_requests(self):
        """Returns a list of stale requests associated with the task's agency"""
        if hasattr(self.agency, 'stale_requests_'):
            return self.agency.stale_requests_
        return FOIARequest.objects.get_stale(agency=self.agency)

    def latest_response(self):
        """Returns the latest response from the agency"""
        foias = self.agency.foiarequest_set.all()
        comms = [c for f in foias for c in f.communications.all() if c.response]
        if len(comms) > 0:
            return max(comms, key=lambda x: x.date)
        else:
            return None

    def update_email(self, new_email, foia_list=None):
        """Updates the email on the agency and the provided requests."""
        from muckrock.agency.models import AgencyEmail
        agency_emails = (self.agency.agencyemail_set
                .filter(request_type='primary', email_type='to'))
        for agency_email in agency_emails:
            agency_email.request_type = 'none'
            agency_email.email_type = 'none'
            agency_email.save()
        AgencyEmail.objects.create(
                email=new_email,
                agency=self.agency,
                request_type='primary',
                email_type='to',
                )
        for foia in foia_list:
            foia.email = new_email
            foia.followup()


class ReviewAgencyTask(Task):
    """An agency has had one of its forms of communication have an error
    and new contact information is required"""
    type = 'ReviewAgencyTask'
    agency = models.ForeignKey('agency.Agency')

    def __unicode__(self):
        return u'Review Agency Task'

    def get_absolute_url(self):
        return reverse('review-agency-task', kwargs={'pk': self.pk})

    def get_review_data(self):
        """Get all the data on all open requests for the agency"""
        review_data = []

        def get_data(open_requests, email_or_fax):
            """Helper function to get email or fax data"""
            if email_or_fax == 'email':
                error_model = EmailError
                comm_model = EmailCommunication
                comm_to_attr = 'to_emails'
            elif email_or_fax == 'fax':
                error_model = FaxError
                comm_model = FaxCommunication
                comm_to_attr = 'to_number'

            review_data = []
            for addr, foias in groupby(open_requests, lambda f: getattr(f, email_or_fax)):
                last_error = error_model.objects.filter(recipient=addr).last()
                last_confirm = (comm_model.objects
                        .filter(**{comm_to_attr: addr})
                        .exclude(confirmed_datetime=None)
                        .order_by('confirmed_datetime')
                        .last()
                        )
                if email_or_fax == 'email':
                    last_open = EmailOpen.objects.filter(recipient=addr).last()
                else:
                    last_open = None
                review_data.append({
                        'address': addr,
                        'error': addr.status == 'error',
                        'foias': list(foias),
                        'total_errors': error_model.objects.filter(recipient=addr).count(),
                        'last_error': last_error.datetime if last_error else None,
                        'last_confirm': last_confirm.confirmed_datetime if last_confirm else None,
                        'last_open': last_open.datetime if last_open else None,
                        'checkbox_name': '%d-%s-%d' % (self.pk, email_or_fax, addr.pk),
                        })
            return review_data

        open_requests = (self.agency.foiarequest_set
                .get_open()
                .order_by('email__status', 'email')
                .exclude(email=None)
                )
        review_data.extend(get_data(open_requests, 'email'))
        open_requests = (self.agency.foiarequest_set
                .get_open()
                .order_by('fax__status', 'fax')
                .exclude(fax=None)
                .exclude(email__status='good')
                )
        review_data.extend(get_data(open_requests, 'fax'))
        foias = list(self.agency.foiarequest_set
                .get_open()
                .exclude(email=None)
                .exclude(fax=None)
                )
        if foias:
            review_data.append({
                    'address': 'Snail Mail',
                    'foias': foias,
                    'checkbox_name': '%d-snail' % self.pk,
                    })

        return review_data


class FlaggedTask(Task):
    """A user has flagged a request, agency or jurisdiction"""
    type = 'FlaggedTask'
    text = models.TextField()
    user = models.ForeignKey(User, blank=True, null=True)
    foia = models.ForeignKey('foia.FOIARequest', blank=True, null=True)
    agency = models.ForeignKey('agency.Agency', blank=True, null=True)
    jurisdiction = models.ForeignKey(Jurisdiction, blank=True, null=True)

    def __unicode__(self):
        return u'Flagged Task'

    def get_absolute_url(self):
        return reverse('flagged-task', kwargs={'pk': self.pk})

    def flagged_object(self):
        """Return the object that was flagged (should only ever be one, and never none)"""
        if self.foia:
            return self.foia
        elif self.agency:
            return self.agency
        elif self.jurisdiction:
            return self.jurisdiction
        else:
            raise AttributeError('No flagged object.')

    def reply(self, text):
        """Send an email reply to the user that raised the flag."""
        support.delay(self.user, text, self)


class ProjectReviewTask(Task):
    """Created when a project is published and needs approval."""
    type = 'ProjectReviewTask'
    project = models.ForeignKey('project.Project')
    notes = models.TextField(blank=True)

    def __unicode__(self):
        return u'Project Review Task'

    def get_absolute_url(self):
        return reverse('projectreview-task', kwargs={'pk': self.pk})

    def reply(self, text, action='reply'):
        """Send an email reply to the user that raised the flag."""
        send_to = [contributor.email for contributor in self.project.contributors.all()]
        project_email = TemplateEmail(
            to=send_to,
            extra_context={'action': action, 'message': text, 'task': self},
            subject=u'%s %s' % (self.project, action),
            text_template='message/project/%s.txt' % action,
            html_template='message/project/%s.html' % action
        )
        project_email.send(fail_silently=False)
        return project_email

    def approve(self, text):
        """Mark the project approved and notify the user."""
        self.project.approved = True
        self.project.save()
        return self.reply(text, 'approved')

    def reject(self, text):
        """Mark the project private and notify the user."""
        self.project.private = True
        self.project.save()
        return self.reply(text, 'rejected')


class NewAgencyTask(Task):
    """A new agency has been created and needs approval"""
    type = 'NewAgencyTask'
    user = models.ForeignKey(User, blank=True, null=True)
    agency = models.ForeignKey('agency.Agency')
    objects = NewAgencyTaskQuerySet.as_manager()

    def __unicode__(self):
        return u'New Agency Task'

    def get_absolute_url(self):
        return reverse('new-agency-task', kwargs={'pk': self.pk})

    def approve(self):
        """Approves agency, resends pending requests to it"""
        self.agency.status = 'approved'
        self.agency.save()
        # resubmit each foia associated to this agency
        for foia in self.agency.foiarequest_set.exclude(status='started'):
            if foia.communications.exists():
                foia.submit(clear=True)

    def reject(self, replacement_agency):
        """Resends pending requests to replacement agency"""
        self.agency.status = 'rejected'
        self.agency.save()
        for foia in self.agency.foiarequest_set.all():
            # first switch foia to use replacement agency
            foia.agency = replacement_agency
            foia.save(comment='new agency task')
            if foia.communications.exists() and foia.status != 'started':
                foia.submit(clear=True)


class ResponseTask(Task):
    """A response has been received and needs its status set"""
    type = 'ResponseTask'
    communication = models.ForeignKey('foia.FOIACommunication')
    created_from_orphan = models.BooleanField(default=False)
    # for predicting statuses
    predicted_status = models.CharField(max_length=10, choices=STATUS, blank=True, null=True)
    status_probability = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return u'Response Task'

    def get_absolute_url(self):
        return reverse('response-task', kwargs={'pk': self.pk})

    def move(self, foia_pks):
        """Moves the associated communication to a new request"""
        return self.communication.move(foia_pks)

    def set_tracking_id(self, tracking_id, comms=None):
        """Sets the tracking ID of the communication's request"""
        if type(tracking_id) is not type(unicode()):
            raise ValueError('Tracking ID should be a unicode string.')
        if comms is None:
            comms = [self.communication]
        for comm in comms:
            if not comm.foia:
                raise ValueError('The task communication is an orphan.')
            foia = comm.foia
            foia.tracking_id = tracking_id
            foia.save(comment='response task tracking id')

    def set_status(self, status, set_foia=True, comms=None):
        """Sets status of comm and foia, with option for only setting comm stats"""
        # check that status is valid
        if status not in [status_set[0] for status_set in STATUS]:
            raise ValueError('Invalid status.')
        if comms is None:
            comms = [self.communication]
        for comm in comms:
            # save comm first
            comm.status = status
            comm.save()
            # save foia next, unless just updating comm status
            if set_foia:
                foia = comm.foia
                foia.status = status
                if status in ['rejected', 'no_docs', 'done', 'abandoned']:
                    foia.date_done = comm.date
                foia.update()
                foia.save(comment='response task status')
                logging.info('Request #%d status changed to "%s"', foia.id, status)
                action = generate_status_action(foia)
                foia.notify(action)
                # Mark generic '<Agency> sent a communication to <FOIARequest> as read.'
                # https://github.com/MuckRock/muckrock/issues/1003
                generic_notifications = (Notification.objects.for_object(foia)
                                        .get_unread().filter(action__verb='sent a communication'))
                for generic_notification in generic_notifications:
                    generic_notification.mark_read()

    def set_price(self, price, comms=None):
        """Sets the price of the communication's request"""
        price = float(price)
        if comms is None:
            comms = [self.communication]
        for comm in comms:
            if not comm.foia:
                raise ValueError('This tasks\'s communication is an orphan.')
            foia = comm.foia
            foia.price = price
            foia.save(comment='response task price')

    def set_date_estimate(self, date_estimate, comms=None):
        """Sets the estimated completion date of the communication's request."""
        if comms is None:
            comms = [self.communication]
        for comm in comms:
            foia = comm.foia
            foia.date_estimate = date_estimate
            foia.update()
            foia.save(comment='response task date estimate')
            logging.info('Estimated completion date set to %s', date_estimate)

    def proxy_reject(self, comms=None):
        """Special handling for a proxy reject"""
        if comms is None:
            comms = [self.communication]
        for comm in comms:
            comm.status = 'rejected'
            comm.save()
            foia = comm.foia
            foia.status = 'rejected'
            foia.proxy_reject()
            foia.update()
            foia.save(comment='response task proxy reject')
            action = generate_status_action(foia)
            foia.notify(action)


class FailedFaxTask(Task):
    """
    Deprecated: keeping this model around to not lose historical data
    A fax for this communication failed"""
    type = 'FailedFaxTask'
    communication = models.ForeignKey('foia.FOIACommunication')
    reason = models.CharField(max_length=255, blank=True, default='')

    def __unicode__(self):
        return u'Failed Fax Task'

    def get_absolute_url(self):
        return reverse('failed-fax-task', kwargs={'pk': self.pk})


class StatusChangeTask(Task):
    """A user has changed the status on a request"""
    type = 'StatusChangeTask'
    user = models.ForeignKey(User)
    old_status = models.CharField(max_length=255)
    foia = models.ForeignKey('foia.FOIARequest')

    def __unicode__(self):
        return u'Status Change Task'

    def get_absolute_url(self):
        return reverse('status-change-task', kwargs={'pk': self.pk})


class CrowdfundTask(Task):
    """Created when a crowdfund is finished"""
    type = 'CrowdfundTask'
    crowdfund = models.ForeignKey('crowdfund.Crowdfund')

    def __unicode__(self):
        return u'Crowdfund Task'

    def get_absolute_url(self):
        return reverse('crowdfund-task', kwargs={'pk': self.pk})


class MultiRequestTask(Task):
    """Created when a multirequest is created and needs approval."""
    type = 'MultiRequestTask'
    multirequest = models.ForeignKey('foia.FOIAMultiRequest')

    def __unicode__(self):
        return u'Multi-Request Task'

    def get_absolute_url(self):
        return reverse('multirequest-task', kwargs={'pk': self.pk})

    def submit(self, agency_list):
        """Submit the multirequest"""
        from muckrock.foia.tasks import submit_multi_request
        return_requests = 0
        for agency in self.multirequest.agencies.all():
            if str(agency.pk) not in agency_list:
                self.multirequest.agencies.remove(agency)
                return_requests += 1
        self.multirequest.save()
        self._return_requests(return_requests)
        submit_multi_request.apply_async(args=(self.multirequest.pk,))

    def reject(self):
        """Reject the multirequest and return the user their requests"""
        self._return_requests(self.multirequest.agencies.count())
        self.multirequest.status = 'started'
        self.multirequest.save()

    def _return_requests(self, num_requests):
        """Return some number of requests to the user"""
        return_amts = self._calc_return_requests(num_requests)
        self._do_return_requests(return_amts)

    def _calc_return_requests(self, num_requests):
        """Determine how many of each type of request to return"""
        num_reg = self.multirequest.num_reg_requests
        num_monthly = self.multirequest.num_monthly_requests
        num_org = self.multirequest.num_org_requests
        if num_requests > (num_reg + num_monthly + num_org):
            # if the number of requests to return is greater than the num of
            # requests logged on the multirequest, just compensate with regular
            # requests - this should only happen for returns on requests created
            # before multi's started tracking where the requests came from
            return {
                    'reg': num_requests - num_monthly - num_org,
                    'monthly': num_monthly,
                    'org': num_org,
                    }
        elif num_requests > (num_reg + num_monthly):
            return {
                    'reg': num_reg,
                    'monthly': num_monthly,
                    'org': num_requests - num_reg - num_monthly,
                    }
        elif num_requests > num_reg:
            return {
                    'reg': num_reg,
                    'monthly': num_requests - num_reg,
                    'org': 0,
                    }
        else:
            return {
                    'reg': num_requests,
                    'monthly': 0,
                    'org': 0,
                    }

    def _do_return_requests(self, return_amts):
        """Update request count on the profile and multirequest given the amounts"""
        # remove returned requests from the multirequest
        # use max to ensure all numbers are positive
        self.multirequest.num_reg_requests -= max(return_amts['reg'], 0)
        self.multirequest.num_monthly_requests -= max(return_amts['monthly'], 0)
        self.multirequest.num_org_requests -= max(return_amts['org'], 0)
        self.multirequest.save()

        # add the return requests to the user's profile
        profile = self.multirequest.user.profile
        profile.num_requests += return_amts['reg']
        profile.get_monthly_requests()
        profile.monthly_requests += return_amts['monthly']
        if profile.organization:
            profile.organization.get_requests()
            profile.organization.num_requests += return_amts['org']
            profile.organization.save()
        else:
            profile.monthly_requests += return_amts['org']
        profile.save()


class NewExemptionTask(Task):
    """Created when a new exemption is submitted for our review."""
    type = 'NewExemptionTask'
    foia = models.ForeignKey('foia.FOIARequest')
    language = models.TextField()
    user = models.ForeignKey(User)

    def __unicode__(self):
        return u'New Exemption Task'

    def get_absolute_url(self):
        return reverse('newexemption-task', kwargs={'pk': self.pk})


# Not a task, but used by tasks
class BlacklistDomain(models.Model):
    """A domain to be blacklisted from sending us emails"""
    domain = models.CharField(max_length=255)

    def __unicode__(self):
        return self.domain

    def resolve_matches(self):
        """Resolves any orphan tasks that match this blacklisted domain."""
        tasks_to_resolve = OrphanTask.objects.get_from_domain(self.domain)
        for task in tasks_to_resolve:
            task.resolve()
