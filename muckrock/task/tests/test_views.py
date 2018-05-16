"""
Tests for Tasks views
"""
# Django
from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase

# Standard Library
import logging

# Third Party
import mock
import nose

# MuckRock
from muckrock.agency.forms import AgencyForm
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.core.test_utils import (
    http_get_response,
    http_post_response,
    mock_middleware,
)
from muckrock.core.views import MRFilterListView
from muckrock.foia.factories import FOIARequestFactory
from muckrock.foia.models import FOIANote
from muckrock.task.factories import (
    FlaggedTaskFactory,
    NewAgencyTaskFactory,
    OrphanTaskFactory,
    ProjectReviewTaskFactory,
    ResponseTaskFactory,
    SnailMailTaskFactory,
)
from muckrock.task.forms import FlaggedTaskForm, ProjectReviewTaskForm
from muckrock.task.models import (
    BlacklistDomain,
    NewAgencyTask,
    OrphanTask,
    SnailMailTask,
)
from muckrock.task.views import (
    FlaggedTaskList,
    ProjectReviewTaskList,
    ResponseTaskList,
    TaskList,
)

eq_ = nose.tools.eq_
ok_ = nose.tools.ok_
raises = nose.tools.raises
mock_send = mock.Mock()

# pylint: disable=missing-docstring


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class TaskListViewTests(TestCase):
    """Test that the task list view resolves and renders correctly."""

    def setUp(self):
        self.url = reverse('response-task-list')
        self.view = ResponseTaskList.as_view()
        self.user = UserFactory(is_staff=True)
        self.task = ResponseTaskFactory()

    def test_login_required(self):
        response = http_get_response(self.url, self.view, follow=True)
        eq_(response.status_code, 302)
        eq_(response.url, '/accounts/login/?next=%s' % self.url)

    def test_not_staff_not_ok(self):
        response = http_get_response(
            self.url, self.view, UserFactory(), follow=True
        )
        eq_(response.status_code, 302)
        eq_(response.url, '/accounts/login/?next=%s' % self.url)

    def test_staff_ok(self):
        response = http_get_response(
            self.url, self.view, self.user, follow=True
        )
        eq_(
            response.status_code, 200,
            (
                'Should respond to staff requests for task list page with 200.'
                ' Actually responds with %d' % response.status_code
            )
        )

    def test_class_inheritance(self):
        actual = TaskList.__bases__
        expected = MRFilterListView().__class__
        ok_(
            expected in actual,
            'Task list should inherit from MRFilterListView class'
        )

    def test_render_task_list(self):
        """The list should have rendered task widgets in its object_list context variable"""
        response = http_get_response(
            self.url, self.view, self.user, follow=True
        )
        obj_list = response.context_data['object_list']
        ok_(obj_list, 'Object list should not be empty.')


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class TaskListViewPOSTTests(TestCase):
    """Tests POST requests to the Task list view"""

    # we have to get the task again if we want to see the updated value

    def setUp(self):
        self.url = reverse('response-task-list')
        self.view = ResponseTaskList.as_view()
        self.user = UserFactory(is_staff=True)
        self.task = ResponseTaskFactory()

    def test_post_resolve_task(self):
        data = {'resolve': 'truthy', 'task': self.task.pk}
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        eq_(
            self.task.resolved, True,
            'Tasks should be resolved by posting the task ID with a "resolve" request.'
        )
        eq_(
            self.task.resolved_by, self.user,
            'Task should record the logged in user who resolved it.'
        )

    def test_post_do_not_resolve_task(self):
        self.client.post(self.url, {'task': self.task.pk})
        self.task.refresh_from_db()
        eq_(
            self.task.resolved, False,
            'Tasks should not be resolved when no "resolve" data is POSTed.'
        )


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class TaskListViewBatchedPOSTTests(TestCase):
    """Tests batched POST requests for all tasks"""

    # we have to get the task again if we want to see the updated value

    def setUp(self):
        self.url = reverse('response-task-list')
        self.view = ResponseTaskList.as_view()
        self.user = UserFactory(is_staff=True)
        task1 = ResponseTaskFactory()
        task2 = ResponseTaskFactory()
        task3 = ResponseTaskFactory()
        self.tasks = [task1, task2, task3]

    def test_batch_resolve_tasks(self):
        data = {
            'resolve': 'truthy',
            'tasks': [_task.id for _task in self.tasks]
        }
        http_post_response(self.url, self.view, data, self.user)
        for _task in self.tasks:
            _task.refresh_from_db()
            eq_(
                _task.resolved, True,
                'Task %d should be resolved when doing a batched resolve' %
                _task.pk
            )


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class OrphanTaskViewTests(TestCase):
    """Tests OrphanTask-specific POST handlers"""

    def setUp(self):
        self.url = reverse('orphan-task-list')
        self.task = OrphanTaskFactory(
            communication__email__from_email__email='test@example.com',
            communication__likely_foia=FOIARequestFactory(),
        )
        UserFactory(username='adam', password='abc', is_staff=True)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_get_single(self):
        """Should be able to view a single task"""
        response = self.client.get(
            reverse('orphan-task', kwargs={
                'pk': self.task.pk
            })
        )
        eq_(response.status_code, 200)

    def test_get_single_404(self):
        """If the single orphan task does not exist, then 404"""
        response = self.client.get(
            reverse('orphan-task', kwargs={
                'pk': 123456789
            })
        )
        eq_(response.status_code, 404)

    def test_move(self):
        foias = FOIARequestFactory.create_batch(2)
        foia_1_comm_count = foias[0].communications.all().count()
        foia_2_comm_count = foias[1].communications.all().count()
        starting_date = self.task.communication.datetime
        self.client.post(
            self.url,
            {
                'move': True,
                'foia_pks': ', '.join(str(f.pk) for f in foias),
                'task': self.task.pk,
            },
        )
        updated_foia_1_comm_count = foias[0].communications.all().count()
        updated_foia_2_comm_count = foias[1].communications.all().count()
        updated_task = OrphanTask.objects.get(pk=self.task.pk)
        ending_date = updated_task.communication.datetime
        ok_(
            updated_task.resolved,
            'Orphan task should be resolved by posting the FOIA pks and task ID.'
        )
        eq_(
            updated_foia_1_comm_count, foia_1_comm_count + 1,
            'Communication should be added to FOIA'
        )
        eq_(
            updated_foia_2_comm_count, foia_2_comm_count + 1,
            'Communication should be added to FOIA'
        )
        eq_(
            starting_date, ending_date,
            'The date of the communication should not change.'
        )

    def test_reject(self):
        self.client.post(self.url, {'reject': True, 'task': self.task.pk})
        updated_task = OrphanTask.objects.get(pk=self.task.pk)
        eq_(
            updated_task.resolved, True, (
                'Orphan task should be rejected by posting any'
                ' truthy value to the "reject" parameter and task ID.'
            )
        )

    def test_reject_despite_likely_foia(self):
        likely_foia = self.task.communication.likely_foia
        comm_count = likely_foia.communications.all().count()
        ok_(
            likely_foia, 'Communication should have a likely FOIA for this test'
        )
        self.client.post(
            self.url, {
                'move': likely_foia.pk,
                'reject': 'true',
                'task': self.task.pk
            }
        )
        updated_comm_count = likely_foia.communications.all().count()
        eq_(
            comm_count, updated_comm_count,
            'Rejecting an orphan with a likely FOIA should not move'
            ' the communication to that FOIA'
        )

    def test_reject_and_blacklist(self):
        self.client.post(
            self.url, {
                'reject': 'true',
                'blacklist': True,
                'task': self.task.pk,
            }
        )
        ok_(BlacklistDomain.objects.filter(domain='example.com'))


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class SnailMailTaskViewTests(TestCase):
    """Tests SnailMailTask-specific POST handlers"""

    def setUp(self):
        self.url = reverse('snail-mail-task-list')
        self.task = SnailMailTaskFactory()
        UserFactory(username='adam', password='abc', is_staff=True)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_get_single(self):
        """Should be able to view a single task"""
        response = self.client.get(
            reverse('snail-mail-task', kwargs={
                'pk': self.task.pk
            })
        )
        eq_(response.status_code, 200)

    def test_post_set_status(self):
        """Should update the status of the task's communication and associated
        request.
        """
        new_status = 'ack'
        self.client.post(
            self.url,
            {
                'status': new_status,
                'task': self.task.pk,
                'save': True,
            },
        )
        updated_task = SnailMailTask.objects.get(pk=self.task.pk)
        eq_(updated_task.communication.status, new_status)
        eq_(updated_task.communication.foia.status, new_status)

    def test_post_record_check(self):
        """A payment snail mail task should record the check number."""
        check_number = 42
        self.task.category = 'p'
        self.task.save()
        self.client.post(
            self.url, {
                'status': 'ack',
                'check_number': check_number,
                'task': self.task.pk,
                'save': True,
            }
        )
        self.task.refresh_from_db()
        note = FOIANote.objects.filter(foia=self.task.communication.foia
                                       ).first()
        ok_(note, 'A note should be generated.')


@mock.patch('muckrock.task.models.FlaggedTask.reply')
class FlaggedTaskViewTests(TestCase):
    """Tests FlaggedTask POST handlers"""

    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.url = reverse('flagged-task-list')
        self.view = FlaggedTaskList.as_view()
        self.task = FlaggedTaskFactory()
        self.request_factory = RequestFactory()

    def test_get_single(self, mock_reply):
        """Should be able to view a single task"""
        # pylint: disable=unused-argument
        request = self.request_factory.get(
            reverse('flagged-task', kwargs={
                'pk': self.task.pk
            })
        )
        request.user = self.user
        request = mock_middleware(request)
        response = self.view(request)
        eq_(response.status_code, 200)

    def post_request(self, data):
        """Helper to post data and get a response"""
        request = self.request_factory.post(self.url, data)
        request.user = self.user
        request = mock_middleware(request)
        response = self.view(request)
        return response

    def test_post_reply(self, mock_reply):
        """Staff should be able to reply to the user who raised the flag"""
        test_text = 'Lorem ipsum'
        form = FlaggedTaskForm({'text': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'reply': 'truthy', 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        ok_(
            not self.task.resolved,
            'The task should not automatically resolve when replying.'
        )
        mock_reply.assert_called_with(test_text)

    def test_post_reply_resolve(self, mock_reply):
        """The task should optionally resolve when replying"""
        test_text = 'Lorem ipsum'
        form = FlaggedTaskForm({'text': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({
            'reply': 'truthy',
            'resolve': True,
            'task': self.task.pk
        })
        self.post_request(post_data)
        self.task.refresh_from_db()
        ok_(self.task.resolved, 'The task should resolve.')
        mock_reply.assert_called_with(test_text)


@mock.patch('muckrock.task.models.ProjectReviewTask.reply')
class ProjectReviewTaskViewTests(TestCase):
    """Tests FlaggedTask POST handlers"""

    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.url = reverse('projectreview-task-list')
        self.view = ProjectReviewTaskList.as_view()
        self.task = ProjectReviewTaskFactory()
        self.request_factory = RequestFactory()

    def test_get_single(self, mock_reply):
        """Should be able to view a single task"""
        # pylint: disable=unused-argument
        _url = reverse('projectreview-task', kwargs={'pk': self.task.pk})
        request = self.request_factory.get(_url)
        request.user = self.user
        request = mock_middleware(request)
        response = self.view(request)
        eq_(response.status_code, 200)

    def post_request(self, data):
        """Helper to post data and get a response"""
        request = self.request_factory.post(self.url, data)
        request.user = self.user
        request = mock_middleware(request)
        response = self.view(request)
        return response

    def test_post_reply(self, mock_reply):
        """Staff should be able to reply to the user who raised the flag"""
        test_text = 'Lorem ipsum'
        form = ProjectReviewTaskForm({'reply': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'action': 'reply', 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        ok_(
            not self.task.resolved,
            'The task should not automatically resolve when replying.'
        )
        mock_reply.assert_called_with(test_text)

    def test_post_reply_approve(self, mock_reply):
        """The task should optionally resolve when replying"""
        test_text = 'Lorem ipsum'
        form = ProjectReviewTaskForm({'reply': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'action': 'approve', 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        self.task.project.refresh_from_db()
        ok_(self.task.project.approved, 'The project should be approved.')
        ok_(self.task.resolved, 'The task should be resolved.')
        mock_reply.assert_called_with(test_text, 'approved')

    def test_post_reply_reject(self, mock_reply):
        """The task should optionally resolve when replying"""
        test_text = 'Lorem ipsum'
        form = ProjectReviewTaskForm({'reply': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'action': 'reject', 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        self.task.project.refresh_from_db()
        ok_(self.task.project.private, 'The project should be made private.')
        ok_(self.task.resolved, 'The task should be resolved.')
        mock_reply.assert_called_with(test_text, 'rejected')


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class NewAgencyTaskViewTests(TestCase):
    """Tests NewAgencyTask-specific POST handlers"""

    def setUp(self):
        self.url = reverse('new-agency-task-list')
        self.task = NewAgencyTaskFactory(agency__status='pending')
        UserFactory(username='adam', password='abc', is_staff=True)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_get_single(self):
        """Should be able to view a single task"""
        response = self.client.get(
            reverse('new-agency-task', kwargs={
                'pk': self.task.pk
            })
        )
        eq_(response.status_code, 200)

    def test_post_accept(self):
        contact_data = {
            'name': 'Test Agency',
            'address_street': '1234 Whatever Street',
            'email': 'who.cares@whatever.com',
            'portal_type': 'other',
            'phone': '',
            'fax': '',
            'jurisdiction': self.task.agency.jurisdiction.pk,
        }
        form = AgencyForm(contact_data, instance=self.task.agency)
        ok_(form.is_valid())
        contact_data.update({'approve': True, 'task': self.task.pk})
        self.client.post(self.url, contact_data)
        updated_task = NewAgencyTask.objects.get(pk=self.task.pk)
        eq_(updated_task.agency.status, 'approved')
        ok_(updated_task.resolved)

    def test_post_reject(self):
        """Rejecting the agency requires a replacement agency"""
        replacement = AgencyFactory()
        self.client.post(
            self.url, {
                'reject': True,
                'task': self.task.pk,
                'replace_agency': replacement.pk,
                'replace_jurisdiction': replacement.jurisdiction.pk,
            }
        )
        updated_task = NewAgencyTask.objects.get(pk=self.task.pk)
        eq_(updated_task.agency.status, 'rejected')
        eq_(updated_task.resolved, True)


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class ResponseTaskListViewTests(TestCase):
    """Tests ResponseTask-specific POST handlers"""

    def setUp(self):
        self.user = UserFactory(is_staff=True)
        self.url = reverse('response-task-list')
        self.view = ResponseTaskList.as_view()
        self.task = ResponseTaskFactory()

    def test_get_list(self):
        """Staff users should be able to view a list of tasks."""
        response = http_get_response(self.url, self.view, self.user)
        eq_(response.status_code, 200)

    def test_get_single(self):
        """Staff users should be able to view a single task"""
        url = reverse('response-task', kwargs={'pk': self.task.pk})
        response = http_get_response(url, self.view, self.user)
        eq_(response.status_code, 200)

    def test_post_set_price(self):
        """Setting the price should update the price on the response's request."""
        price = 1
        foia = self.task.communication.foia
        logging.info(foia.agency)
        data = {
            'status': 'done',
            'price': price,
            'task': self.task.pk,
            'save': True,
        }
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        foia.refresh_from_db()
        eq_(foia.price, float(price), 'The price on the FOIA should be set.')
        ok_(self.task.resolved, 'Setting the price should resolve the task.')

    def test_post_set_status(self):
        """Setting the status should save it to the response and request, then resolve task."""
        status_change = 'done'
        data = {
            'status': status_change,
            'set_foia': True,
            'task': self.task.pk,
            'save': True,
        }
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        self.task.communication.foia.refresh_from_db()
        comm_status = self.task.communication.status
        foia_status = self.task.communication.foia.status
        eq_(
            comm_status, status_change,
            'The status change should be saved to the communication.'
        )
        eq_(foia_status, status_change, 'The status of the FOIA should be set.')
        eq_(
            self.task.resolved, True,
            'Setting the status should resolve the task'
        )

    def test_post_set_comm_status(self):
        """Setting the status on just the communication should not influence its request."""
        status_change = 'done'
        existing_foia_status = self.task.communication.foia.status
        data = {
            'status': status_change,
            'set_foia': False,
            'task': self.task.pk,
            'save': True,
        }
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        self.task.communication.foia.refresh_from_db()
        comm_status = self.task.communication.status
        foia_status = self.task.communication.foia.status
        eq_(
            comm_status, status_change,
            'The status change should be saved to the communication.'
        )
        eq_(
            foia_status, existing_foia_status,
            'The status of the FOIA should not be changed.'
        )
        eq_(
            self.task.resolved, True,
            'Settings the status should resolve the task.'
        )

    def test_post_tracking_number(self):
        """Setting the tracking number should save it to the response's request."""
        new_tracking_id = 'ABC123OMGWTF'
        data = {
            'tracking_number': new_tracking_id,
            'status': 'done',
            'task': self.task.pk,
            'save': True,
        }
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        self.task.communication.foia.refresh_from_db()
        foia_tracking = self.task.communication.foia.current_tracking_id()
        eq_(
            foia_tracking, new_tracking_id,
            'The new tracking number should be saved to the associated request.'
        )
        ok_(
            self.task.resolved,
            'Setting the tracking number should resolve the task'
        )

    def test_post_move(self):
        """Moving the response should save it to a new request."""
        other_foia = FOIARequestFactory()
        starting_date = self.task.communication.datetime
        data = {
            'move': other_foia.id,
            'status': 'done',
            'task': self.task.pk,
            'save': True,
        }
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        ending_date = self.task.communication.datetime
        eq_(
            self.task.communication.foia, other_foia,
            'The response should be moved to a different FOIA.'
        )
        ok_(self.task.resolved, 'Moving the status should resolve the task')
        eq_(
            starting_date, ending_date,
            'Moving the communication should not change its date.'
        )

    def test_post_move_multiple(self):
        """Moving the response to multiple requests modify all the requests."""
        other_foias = [
            FOIARequestFactory(),
            FOIARequestFactory(),
            FOIARequestFactory()
        ]
        move_to_ids = ', '.join([str(foia.id) for foia in other_foias])
        change_status = 'done'
        change_tracking = 'DEADBEEF'
        data = {
            'move': move_to_ids,
            'status': change_status,
            'tracking_number': change_tracking,
            'task': self.task.pk,
            'save': True,
        }
        http_post_response(self.url, self.view, data, self.user)
        for foia in other_foias:
            foia.refresh_from_db()
            eq_(
                change_tracking, foia.current_tracking_id(),
                'Tracking should update for each request in move list.'
            )

    def test_terrible_data(self):
        """Posting awful data shouldn't cause everything to collapse."""
        data = {
            'move': 'omglol, howru',
            'status': 'notastatus',
            'tracking_number': ['wtf'],
            'task': self.task.pk
        }
        response = http_post_response(self.url, self.view, data, self.user)
        ok_(response)

    def test_foia_integrity(self):
        """
        Updating a request through a task should maintain integrity of that request's data.
        This is in response to issue #387.
        """
        # first saving a comm
        foia = self.task.communication.foia
        num_comms = foia.communications.count()
        foia.create_out_communication(
            from_user=foia.user,
            text='Just testing',
            user=foia.user,
        )
        eq_(
            foia.communications.count(), num_comms + 1,
            'Should add a new communication to the FOIA.'
        )
        num_comms = foia.communications.count()
        # next try resolving the task with a tracking number set
        data = {
            'resolve': 'true',
            'tracking_number': u'12345',
            'task': self.task.pk
        }
        http_post_response(self.url, self.view, data, self.user)
        foia.refresh_from_db()
        eq_(
            foia.communications.count(), num_comms,
            'The number of communications should not have changed from before.'
        )
