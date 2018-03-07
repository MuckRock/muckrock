"""
Tests for Tasks models
"""

# Django
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase
from django.utils import timezone

# Standard Library
import logging

# Third Party
import mock
import nose

# MuckRock
from muckrock import factories, task
from muckrock.communication.models import EmailAddress
from muckrock.foia.models import FOIANote, FOIARequest
from muckrock.task.factories import FlaggedTaskFactory, ProjectReviewTaskFactory
from muckrock.task.signals import domain_blacklist

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises
mock_send = mock.Mock()

# pylint: disable=missing-docstring
# pylint: disable=line-too-long
# pylint: disable=protected-access


class TaskTests(TestCase):
    """Test the Task base class"""

    def setUp(self):
        self.task = task.models.Task.objects.create()

    def test_task_creates_successfully(self):
        ok_(self.task, 'Tasks given no arguments should create successfully')

    def test_unicode(self):
        eq_(
            unicode(self.task), u'Task',
            'Unicode string should return the classname of the task'
        )

    def test_resolve(self):
        """Tasks should be resolvable, updating their state when that happens."""
        self.task.resolve()
        ok_(
            self.task.resolved is True,
            'Resolving task should set resolved field to True'
        )
        ok_(
            self.task.date_done is not None,
            'Resolving task should set date_done'
        )
        ok_(
            self.task.resolved_by is None,
            'Resolving without providing a user should leave the field blank.'
        )

    def test_resolve_with_user(self):
        """Tasks should record the user responsible for the resolution."""
        user = factories.UserFactory()
        self.task.resolve(user)
        eq_(
            self.task.resolved_by, user,
            'The resolving user should be recorded by the task.'
        )


class OrphanTaskTests(TestCase):
    """Test the OrphanTask class"""

    def setUp(self):
        self.comm = factories.FOIACommunicationFactory(
            email__from_email__email='test@example.com',
        )
        self.task = task.models.OrphanTask.objects.create(
            reason='ib', communication=self.comm, address='Whatever Who Cares'
        )
        self.user = factories.UserFactory()

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse('orphan-task', kwargs={
                'pk': self.task.pk
            })
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            'Orphan tasks given reason and communication arguments should create successfully'
        )

    def test_move(self):
        """Should move the communication to the listed requests and create a ResponseTask for each new communication."""
        foia1 = factories.FOIARequestFactory()
        foia2 = factories.FOIARequestFactory()
        foia3 = factories.FOIARequestFactory()
        count_response_tasks = task.models.ResponseTask.objects.count()
        self.task.move([foia1.pk, foia2.pk, foia3.pk], self.user)
        eq_(
            task.models.ResponseTask.objects.count(), count_response_tasks + 3,
            'Reponse tasks should be created for each communication moved.'
        )

    def test_get_sender_domain(self):
        """Should return the domain of the orphan's sender."""
        eq_(self.task.get_sender_domain(), 'example.com')

    def test_reject(self):
        """Shouldn't do anything, ATM. Revisit later."""
        self.task.reject()

    def test_blacklist(self):
        """A blacklisted orphan should add its sender's domain to the blacklist"""
        self.task.blacklist()
        ok_(task.models.BlacklistDomain.objects.filter(domain='example.com'))

    def test_blacklist_duplicate(self):
        """The blacklist method should not crash when a domain is dupliacted."""
        task.models.BlacklistDomain.objects.create(domain='muckrock.com')
        task.models.BlacklistDomain.objects.create(domain='muckrock.com')
        self.task.blacklist()
        ok_(task.models.BlacklistDomain.objects.filter(domain='muckrock.com'))

    def test_resolve_after_blacklisting(self):
        """After blacklisting, other orphan tasks from the sender should be resolved."""
        other_task = task.models.OrphanTask.objects.create(
            reason='ib', communication=self.comm, address='Whatever Who Cares'
        )
        self.task.blacklist()
        self.task.refresh_from_db()
        other_task.refresh_from_db()
        ok_(self.task.resolved and other_task.resolved)

    def test_create_blacklist_sender(self):
        """An orphan created from a blacklisted sender should be automatically resolved."""
        self.task.blacklist()
        self.task.refresh_from_db()
        ok_(self.task.resolved)
        new_orphan = task.models.OrphanTask.objects.create(
            reason='ib', communication=self.comm, address='orphan-address'
        )
        # manually call the method since the signal isn't triggering during testing
        domain_blacklist(task.models.OrphanTask, new_orphan, True)
        new_orphan.refresh_from_db()
        logging.debug(new_orphan.resolved)
        ok_(new_orphan.resolved)


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class FlaggedTaskTests(TestCase):
    """Test the FlaggedTask class"""

    def setUp(self):
        self.task = task.models.FlaggedTask

    def test_get_absolute_url(self):
        text = 'Lorem ipsum'
        user = factories.UserFactory()
        foia = factories.FOIARequestFactory()
        flagged_task = self.task.objects.create(user=user, foia=foia, text=text)
        _url = reverse('flagged-task', kwargs={'pk': flagged_task.pk})
        eq_(flagged_task.get_absolute_url(), _url)

    def test_flagged_object(self):
        """A flagged task should be able to return its object."""
        text = 'Lorem ipsum'
        user = factories.UserFactory()
        foia = factories.FOIARequestFactory()
        agency = factories.AgencyFactory()
        jurisdiction = factories.JurisdictionFactory()
        flagged_foia_task = self.task.objects.create(
            user=user, foia=foia, text=text
        )
        flagged_agency_task = self.task.objects.create(
            user=user, agency=agency, text=text
        )
        flagged_jurisdiction_task = self.task.objects.create(
            user=user, jurisdiction=jurisdiction, text=text
        )
        eq_(flagged_foia_task.flagged_object(), foia)
        eq_(flagged_agency_task.flagged_object(), agency)
        eq_(flagged_jurisdiction_task.flagged_object(), jurisdiction)

    @raises(AttributeError)
    def test_no_flagged_object(self):
        """Should raise an error if no flagged object"""
        text = 'Lorem ipsum'
        user = factories.UserFactory()
        flagged_task = self.task.objects.create(user=user, text=text)
        flagged_task.flagged_object()

    @mock.patch('muckrock.message.tasks.support.delay')
    def test_reply(self, mock_support):
        """Given a message, a support notification should be sent to the task's user."""
        flagged_task = FlaggedTaskFactory()
        reply = 'Lorem ipsum'
        flagged_task.reply(reply)
        mock_support.assert_called_with(flagged_task.user, reply, flagged_task)


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class ProjectReviewTaskTests(TestCase):
    """
    The ProjectReviewTask provides us a way to moderate community projects.
    When it is created, it should notify Slack.
    When it is approved, it should mark its project approved.
    When it is rejected, it should mark its project private.
    It should allow us a way to communicate with the users of this project.
    """

    def setUp(self):
        self.task = ProjectReviewTaskFactory()
        contributor = factories.UserFactory()
        self.task.project.contributors.add(contributor)

    def test_get_aboslute_url(self):
        _url = reverse('projectreview-task', kwargs={'pk': self.task.pk})
        eq_(self.task.get_absolute_url(), _url)

    @mock.patch('muckrock.message.email.TemplateEmail.send')
    def test_reply(self, mock_feedback_send):
        self.task.reply('Lorem ipsum')
        mock_feedback_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.email.TemplateEmail.send')
    def test_approve(self, mock_notification_send):
        """Approving the task should mark it approved and notify the contributors."""
        self.task.approve('Lorem ipsum')
        ok_(self.task.project.approved, 'The project should be approved')
        mock_notification_send.assert_called_with(fail_silently=False)

    @mock.patch('muckrock.message.email.TemplateEmail.send')
    def test_reject(self, mock_notification_send):
        """Rejecting the task should mark it private and notify the contributors."""
        self.task.reject('Lorem ipsum')
        ok_(self.task.project.private, 'The project should be made private.')
        mock_notification_send.assert_called_with(fail_silently=False)


class SnailMailTaskTests(TestCase):
    """Test the SnailMailTask class"""

    def setUp(self):
        self.comm = factories.FOIACommunicationFactory()
        self.task = task.models.SnailMailTask.objects.create(
            category='a', communication=self.comm
        )

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse('snail-mail-task', kwargs={
                'pk': self.task.pk
            })
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            'Snail mail tasks should create successfully given a category and a communication'
        )

    def test_set_status(self):
        new_status = 'ack'
        self.task.set_status(new_status)
        eq_(
            self.task.communication.status, new_status,
            'Setting status should update status of associated communication'
        )
        eq_(
            self.task.communication.foia.status, new_status,
            'Setting status should update status of associated communication\'s foia request'
        )

    def test_update_text(self):
        """Snail mail tasks should be able to update the text of their communication."""
        comm = self.task.communication
        new_text = 'test'
        self.task.update_text(new_text)
        self.task.refresh_from_db()
        comm.refresh_from_db()
        eq_(
            comm.communication, new_text,
            'The text of the communication should be updated.'
        )

    def test_record_check(self):
        """When given a check number, a note should be attached to the request."""
        user = factories.UserFactory(is_staff=True)
        check_number = 1
        self.task.amount = 100.00
        self.task.save()
        note = self.task.record_check(check_number, user)
        ok_(isinstance(note, FOIANote), 'The method should return a FOIANote.')


class StaleAgencyTaskTests(TestCase):
    """Test the StaleAgencyTask class"""

    def setUp(self):
        self.task = task.factories.StaleAgencyTaskFactory()
        self.foia = FOIARequest.objects.filter(agency=self.task.agency).first()

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse('stale-agency-task', kwargs={
                'pk': self.task.pk
            })
        )

    def test_stale_requests(self):
        """
        The stale agency task should provide a list of open requests which have not
        recieved any response since the stale duration
        """
        closed_foia = factories.StaleFOIARequestFactory(
            agency=self.task.agency, status='done'
        )
        no_response = factories.StaleFOIARequestFactory(
            agency=self.task.agency, stale_comm__response=False
        )
        stale_requests = list(self.task.stale_requests())
        ok_(
            self.foia in stale_requests,
            'Open requests should be considered stale.'
        )
        ok_(
            no_response in stale_requests,
            'Requests without any response should be considered stale.'
        )
        ok_(
            closed_foia not in stale_requests,
            'Closed requests should not be considered stale.'
        )

    def test_latest_response(self):
        """
        The stale agency task should provide the most
        recent response received from the agency.
        """
        latest_response = self.task.latest_response()
        eq_(latest_response, self.foia.last_response())
        ok_(latest_response.response, 'Should return a response!')

    @mock.patch('muckrock.foia.models.FOIARequest.followup')
    def test_update_email(self, mock_followup):
        """
        The stale agency task should update the email of its associated
        agency and any selected stale requests. Then, the foias with
        updated emails should automatically follow up with the agency.
        The agency should also have its stale flag lowered.
        """
        new_email = EmailAddress.objects.fetch('test@email.com')
        self.task.update_email(new_email, [self.foia])
        self.task.refresh_from_db()
        eq_(
            self.task.agency.get_emails().first(),
            new_email,
        )
        eq_(self.foia.email, new_email, 'The foia\'s email should be updated.')
        mock_followup.assert_called()

    def test_resolve(self):
        """Resolving the task should lower the stale flag on the agency."""
        self.task.resolve()
        ok_(not self.task.agency.stale, 'The agency should no longer be stale.')


class NewAgencyTaskTests(TestCase):
    """Test the NewAgencyTask class"""

    def setUp(self):
        self.user = factories.UserFactory()
        self.agency = factories.AgencyFactory(status='pending')
        self.task = task.models.NewAgencyTask.objects.create(
            user=self.user, agency=self.agency
        )

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse('new-agency-task', kwargs={
                'pk': self.task.pk
            })
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            'New agency tasks should create successfully given a user and an agency'
        )

    @mock.patch('muckrock.foia.models.FOIARequest.submit')
    def test_approve(self, mock_submit):
        submitted_foia = factories.FOIARequestFactory(
            agency=self.agency, status='submitted'
        )
        factories.FOIACommunicationFactory(foia=submitted_foia)
        drafted_foia = factories.FOIARequestFactory(
            agency=self.agency, status='started'
        )
        factories.FOIACommunicationFactory(foia=drafted_foia)
        self.task.approve()
        eq_(
            self.task.agency.status, 'approved',
            'Approving a new agency should actually, you know, approve the agency.'
        )
        # since we have 1 draft and 1 nondraft FOIA, we should expect submit() to be called once
        eq_(
            mock_submit.call_count, 1,
            'Approving a new agency should resubmit non-draft FOIAs associated with that agency.'
        )

    def test_reject(self):
        replacement = factories.AgencyFactory()
        existing_foia = factories.FOIARequestFactory(agency=self.agency)
        self.task.reject(replacement)
        existing_foia.refresh_from_db()
        eq_(
            self.task.agency.status, 'rejected',
            'Rejecting a new agency should leave it unapproved.'
        )
        eq_(
            existing_foia.agency, replacement,
            'The replacement agency should receive the rejected agency\'s requests.'
        )

    def test_spam(self):
        existing_foia = factories.FOIARequestFactory(
            agency=self.agency,
            status='submitted',
        )
        self.task.spam()
        existing_foia.refresh_from_db()
        eq_(self.agency.status, 'rejected')
        nose.tools.assert_false(self.user.is_active)
        eq_(existing_foia.status, 'started')


class ResponseTaskTests(TestCase):
    """Test the ResponseTask class"""

    def setUp(self):
        agency = factories.AgencyFactory()
        comm = factories.FOIACommunicationFactory(
            response=True, foia__agency=agency
        )
        self.task = task.models.ResponseTask.objects.create(communication=comm)
        self.form = task.forms.ResponseTaskForm()
        self.user = factories.UserFactory()

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse('response-task', kwargs={
                'pk': self.task.pk
            })
        )

    def test_task_creates_successfully(self):
        ok_(
            self.task,
            'Response tasks should creates successfully given a communication'
        )

    def test_set_status_to_ack(self):
        self.form.set_status('ack', True, [self.task.communication])
        eq_(
            self.task.communication.foia.date_done, None,
            'The FOIA should not be set to done if the status does not indicate it is done.'
        )
        eq_(
            self.task.communication.status, 'ack',
            'The communication should be set to the proper status.'
        )
        eq_(
            self.task.communication.foia.status, 'ack',
            'The FOIA should be set to the proper status.'
        )

    def test_set_status_to_done(self):
        self.form.set_status('done', True, [self.task.communication])
        eq_(
            self.task.communication.foia.date_done is None, False,
            'The FOIA should be set to done if the status indicates it is done.'
        )
        eq_(
            self.task.communication.status, 'done',
            'The communication should be set to the proper status.'
        )
        eq_(
            self.task.communication.foia.status, 'done',
            'The FOIA should be set to the proper status.'
        )

    def test_set_comm_status_only(self):
        foia = self.task.communication.foia
        existing_status = foia.status
        self.form.set_status('done', False, [self.task.communication])
        foia.refresh_from_db()
        eq_(
            foia.date_done is None, True,
            'The FOIA should not be set to done because we are not settings its status.'
        )
        eq_(
            foia.status, existing_status,
            'The FOIA status should not be changed.'
        )
        eq_(
            self.task.communication.status, 'done',
            'The Communication status should be changed, however.'
        )

    def test_set_tracking_id(self):
        new_tracking = u'dogs-r-cool'
        self.form.set_tracking_id(new_tracking, [self.task.communication])
        self.task.refresh_from_db()
        eq_(
            self.task.communication.foia.current_tracking_id(), new_tracking,
            'Should update the tracking number on the request.'
        )

    def test_set_date_estimate(self):
        new_date = timezone.now()
        self.form.set_date_estimate(new_date, [self.task.communication])
        eq_(
            self.task.communication.foia.date_estimate, new_date,
            'Should update the estimated completion date on the request.'
        )

    def test_set_price(self):
        price = 1.23
        self.form.set_price(price, [self.task.communication])
        eq_(
            self.task.communication.foia.price, price,
            'Should update the price on the request.'
        )

    def test_move(self):
        move_to_foia = factories.FOIARequestFactory()
        self.form.move_communication(
            self.task.communication, move_to_foia.pk, self.user
        )
        eq_(
            self.task.communication.foia, move_to_foia,
            'Should move the communication to a different request.'
        )

    @raises(ValueError)
    def test_bad_status(self):
        """Should raise an error if given a nonexistant status."""
        self.form.set_status('foo', True, [self.task.communication])

    @raises(ValueError)
    def test_bad_tracking_number(self):
        """Should raise an error if not given a string."""
        self.form.set_tracking_id(['foo'], [self.task.communication])

    @raises(Http404)
    def test_bad_move(self):
        """Should raise a 404 if non-existant move destination."""
        self.form.move_communication(self.task.communication, 111111, self.user)

    @raises(ValueError)
    def test_bad_price(self):
        """Should raise an error if not given a value convertable to a float"""
        self.form.set_price('foo', [self.task.communication])


class TestNewExemptionTask(TestCase):
    """The NewExemptionTask allows staff to review user-submitted exemptions,
    document the use of exemptions, and use them to create new ones."""

    def setUp(self):
        self.task = task.factories.NewExemptionTaskFactory()

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse('newexemption-task', kwargs={
                'pk': self.task.pk
            })
        )


class MultiRequestTaskTests(TestCase):
    """Test the MultiRequestTask class"""

    def setUp(self):
        self.agencies = factories.AgencyFactory.create_batch(6)
        self.organization = factories.OrganizationFactory(num_requests=100)
        self.multi = factories.FOIAMultiRequestFactory(
            status='submitted',
            agencies=self.agencies,
            num_org_requests=1,
            num_monthly_requests=2,
            num_reg_requests=3,
            user__profile__num_requests=5,
            user__profile__monthly_requests=10,
            user__profile__organization=self.organization,
        )
        self.task = task.models.MultiRequestTask.objects.create(
            multirequest=self.multi,
        )

    def test_get_absolute_url(self):
        eq_(
            self.task.get_absolute_url(),
            reverse('multirequest-task', kwargs={
                'pk': self.task.pk
            }),
        )

    def test_submit(self):
        """Test submitting the task"""
        agency_list = [str(a.pk) for a in self.agencies[:4]]
        self.task.submit(agency_list)
        eq_(
            set(self.multi.agencies.all()),
            set(self.agencies[:4]),
        )
        self.multi.refresh_from_db()
        eq_(self.multi.status, 'filed')
        eq_(FOIARequest.objects.filter(multirequest=self.multi).count(), 4)

    def test_reject(self):
        """Test rejecting the request"""
        self.task.reject()
        eq_(
            set(self.multi.agencies.all()),
            set(self.agencies),
        )
        eq_(self.multi.status, 'started')
        eq_(FOIARequest.objects.filter(multirequest=self.multi).count(), 0)

    def test_calc_return_requests(self):
        """Test calculating the return requests"""
        values = [
            (7, 4, 2, 1),
            (6, 3, 2, 1),
            (5, 3, 2, 0),
            (4, 3, 1, 0),
            (3, 3, 0, 0),
            (2, 2, 0, 0),
            (1, 1, 0, 0),
        ]
        for total, reg, monthly, org in values:
            eq_(
                self.task._calc_return_requests(total),
                {
                    'reg': reg,
                    'monthly': monthly,
                    'org': org,
                },
            )

    def test_do_return_requests(self):
        """Test return requests"""
        self.task._do_return_requests({
            'reg': 2,
            'monthly': 0,
            'org': 1,
        })
        eq_(self.multi.num_reg_requests, 1)
        eq_(self.multi.num_monthly_requests, 2)
        eq_(self.multi.num_org_requests, 0)
        eq_(self.multi.user.profile.num_requests, 7)
        eq_(self.multi.user.profile.monthly_requests, 10)
        eq_(self.multi.user.profile.organization.num_requests, 101)


class TestTaskManager(TestCase):
    """Tests for a helpful and handy task object manager."""

    @mock.patch(
        'muckrock.message.notifications.SlackNotification.send', mock_send
    )
    def setUp(self):
        user = factories.UserFactory()
        agency = factories.AgencyFactory(status='pending')
        self.foia = factories.FOIARequestFactory(user=user, agency=agency)
        self.comm = factories.FOIACommunicationFactory(
            foia=self.foia, response=True
        )
        # tasks that incorporate FOIAs are:
        # ResponseTask, SnailMailTask, FlaggedTask,
        # StatusChangeTask, NewAgencyTask
        response_task = task.models.ResponseTask.objects.create(
            communication=self.comm
        )
        snail_mail_task = task.models.SnailMailTask.objects.create(
            category='a', communication=self.comm
        )
        flagged_task = task.models.FlaggedTask.objects.create(
            user=user, text='Halp', foia=self.foia
        )
        status_change_task = task.models.StatusChangeTask.objects.create(
            user=user, old_status='ack', foia=self.foia
        )
        new_agency_task = task.models.NewAgencyTask.objects.create(
            user=user, agency=agency
        )
        self.tasks = [
            response_task, snail_mail_task, flagged_task, status_change_task,
            new_agency_task
        ]

    def test_tasks_for_foia(self):
        """
        The task manager should return all tasks that explictly
        or implicitly reference the provided FOIA.
        """
        staff_user = factories.UserFactory(
            is_staff=True, profile__acct_type='admin'
        )
        returned_tasks = task.models.Task.objects.filter_by_foia(
            self.foia, staff_user
        )
        eq_(
            returned_tasks, self.tasks,
            'The manager should return all the tasks that incorporate this FOIA.'
        )
