"""
Tests for Tasks views
"""
from datetime import datetime

from django.core.urlresolvers import reverse
from django.test import TestCase, Client, RequestFactory

import logging
import mock
import nose

from muckrock import agency, factories, task
from muckrock.communication.models import EmailAddress, EmailCommunication
from muckrock.foia.models import FOIARequest, FOIANote
from muckrock.foia.views import save_foia_comm
from muckrock.task.factories import (
    FlaggedTaskFactory,
    StaleAgencyTaskFactory,
    ResponseTaskFactory,
)
from muckrock.task.views import ResponseTaskList
from muckrock.test_utils import mock_middleware, http_get_response, http_post_response
from muckrock.views import MRFilterListView

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
        self.user = factories.UserFactory(is_staff=True)
        self.task = ResponseTaskFactory()

    def test_login_required(self):
        response = http_get_response(self.url, self.view, follow=True)
        eq_(response.status_code, 302)
        eq_(response.url, '/accounts/login/?next=%s' % self.url)

    def test_not_staff_not_ok(self):
        response = http_get_response(self.url, self.view, factories.UserFactory(), follow=True)
        eq_(response.status_code, 302)
        eq_(response.url, '/accounts/login/?next=%s' % self.url)

    def test_staff_ok(self):
        response = http_get_response(self.url, self.view, self.user, follow=True)
        eq_(response.status_code, 200,
            ('Should respond to staff requests for task list page with 200.'
            ' Actually responds with %d' % response.status_code))

    def test_class_inheritance(self):
        # pylint: disable=no-self-use
        actual = task.views.TaskList.__bases__
        expected = MRFilterListView().__class__
        ok_(expected in actual,
            'Task list should inherit from MRFilterListView class')

    def test_render_task_list(self):
        """The list should have rendered task widgets in its object_list context variable"""
        response = http_get_response(self.url, self.view, self.user, follow=True)
        obj_list = response.context_data['object_list']
        ok_(obj_list, 'Object list should not be empty.')

@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class TaskListViewPOSTTests(TestCase):
    """Tests POST requests to the Task list view"""
    # we have to get the task again if we want to see the updated value

    def setUp(self):
        self.url = reverse('response-task-list')
        self.view = ResponseTaskList.as_view()
        self.user = factories.UserFactory(is_staff=True)
        self.task = ResponseTaskFactory()

    def test_post_resolve_task(self):
        data = {'resolve': 'truthy', 'task': self.task.pk}
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        eq_(self.task.resolved, True,
            'Tasks should be resolved by posting the task ID with a "resolve" request.')
        eq_(self.task.resolved_by, self.user,
            'Task should record the logged in user who resolved it.')

    def test_post_do_not_resolve_task(self):
        self.client.post(self.url, {'task': self.task.pk})
        self.task.refresh_from_db()
        eq_(self.task.resolved, False,
            'Tasks should not be resolved when no "resolve" data is POSTed.')

@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class TaskListViewBatchedPOSTTests(TestCase):
    """Tests batched POST requests for all tasks"""
    # we have to get the task again if we want to see the updated value

    def setUp(self):
        self.url = reverse('response-task-list')
        self.view = ResponseTaskList.as_view()
        self.user = factories.UserFactory(is_staff=True)
        task1 = ResponseTaskFactory()
        task2 = ResponseTaskFactory()
        task3 = ResponseTaskFactory()
        self.tasks = [task1, task2, task3]

    def test_batch_resolve_tasks(self):
        data = {'resolve': 'truthy', 'tasks': [_task.id for _task in self.tasks]}
        http_post_response(self.url, self.view, data, self.user)
        for _task in self.tasks:
            _task.refresh_from_db()
            eq_(_task.resolved, True,
                'Task %d should be resolved when doing a batched resolve' % _task.pk)

@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class OrphanTaskViewTests(TestCase):
    """Tests OrphanTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('orphan-task-list')
        self.task = task.models.OrphanTask.objects.get(pk=2)
        self.task.communication.save()
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_get_single(self):
        """Should be able to view a single task"""
        response = self.client.get(reverse('orphan-task', kwargs={'pk': self.task.pk}))
        eq_(response.status_code, 200)

    def test_get_single_404(self):
        """If the single orphan task does not exist, then 404"""
        response = self.client.get(reverse('orphan-task', kwargs={'pk': 123456789}))
        eq_(response.status_code, 404)

    def test_move(self):
        foia_1_comm_count = FOIARequest.objects.get(pk=1).communications.all().count()
        foia_2_comm_count = FOIARequest.objects.get(pk=2).communications.all().count()
        starting_date = self.task.communication.date
        EmailCommunication.objects.create(
                communication=self.task.communication,
                sent_datetime=datetime.now(),
                from_email=EmailAddress.objects.fetch('test@example.com'),
                )
        self.client.post(self.url, {'move': '1, 2', 'task': self.task.pk})
        updated_foia_1_comm_count = FOIARequest.objects.get(pk=1).communications.all().count()
        updated_foia_2_comm_count = FOIARequest.objects.get(pk=2).communications.all().count()
        updated_task = task.models.OrphanTask.objects.get(pk=self.task.pk)
        ending_date = updated_task.communication.date
        ok_(updated_task.resolved,
            'Orphan task should be resolved by posting the FOIA pks and task ID.')
        eq_(updated_foia_1_comm_count, foia_1_comm_count + 1,
            'Communication should be added to FOIA')
        eq_(updated_foia_2_comm_count, foia_2_comm_count + 1,
            'Communication should be added to FOIA')
        eq_(starting_date, ending_date,
            'The date of the communication should not change.')

    def test_reject(self):
        self.client.post(self.url, {'reject': True, 'task': self.task.pk})
        updated_task = task.models.OrphanTask.objects.get(pk=self.task.pk)
        eq_(updated_task.resolved, True,
                ('Orphan task should be rejected by posting any'
                ' truthy value to the "reject" parameter and task ID.'))

    def test_reject_despite_likely_foia(self):
        likely_foia_pk = self.task.communication.likely_foia.pk
        likely_foia = FOIARequest.objects.get(pk=likely_foia_pk)
        likely_foia_comm_count = likely_foia.communications.all().count()
        ok_(likely_foia_pk,
                'Communication should have a likely FOIA for this test')
        self.client.post(self.url, {
            'move': str(likely_foia_pk),
            'reject': 'true',
            'task': self.task.pk})
        updated_likely_foia_comm_count = likely_foia.communications.all().count()
        eq_(likely_foia_comm_count, updated_likely_foia_comm_count,
                ('Rejecting an orphan with a likely FOIA should not move'
                ' the communication to that FOIA'))

    def test_reject_and_blacklist(self):
        EmailCommunication.objects.create(
                communication=self.task.communication,
                from_email=EmailAddress.objects.fetch('Michael Morisy <michael@muckrock.com>'),
                sent_datetime=datetime.now(),
                )
        self.task.communication.save()
        self.client.post(self.url, {
            'reject': 'true',
            'blacklist': True,
            'task': self.task.pk})
        ok_(task.models.BlacklistDomain.objects.filter(domain='muckrock.com'))

@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class SnailMailTaskViewTests(TestCase):
    """Tests SnailMailTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('snail-mail-task-list')
        self.task = task.models.SnailMailTask.objects.get(pk=3)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_get_single(self):
        """Should be able to view a single task"""
        response = self.client.get(reverse('snail-mail-task', kwargs={'pk': self.task.pk}))
        eq_(response.status_code, 200)

    def test_post_set_status(self):
        """Should update the status of the task's communication and associated request."""
        new_status = 'ack'
        self.client.post(self.url, {'status': new_status, 'task': self.task.pk})
        updated_task = task.models.SnailMailTask.objects.get(pk=self.task.pk)
        eq_(updated_task.communication.status, new_status,
            'Should update status of the communication.')
        eq_(updated_task.communication.foia.status, new_status,
            'Should update the status of the communication\'s associated request.')

    def test_post_record_check(self):
        """A payment snail mail task should record the check number."""
        check_number = 42
        self.task.category = 'p'
        self.task.save()
        self.client.post(self.url, {
            'status': 'ack',
            'check_number': check_number,
            'task': self.task.pk
        })
        self.task.refresh_from_db()
        note = FOIANote.objects.filter(foia=self.task.communication.foia).first()
        ok_(note, 'A note should be generated.')


@mock.patch('muckrock.task.models.FlaggedTask.reply')
class FlaggedTaskViewTests(TestCase):
    """Tests FlaggedTask POST handlers"""
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True)
        self.url = reverse('flagged-task-list')
        self.view = task.views.FlaggedTaskList.as_view()
        self.task = FlaggedTaskFactory()
        self.request_factory = RequestFactory()

    def test_get_single(self, mock_reply):
        """Should be able to view a single task"""
        # pylint: disable=unused-argument
        request = self.request_factory.get(reverse('flagged-task', kwargs={'pk': self.task.pk}))
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
        form = task.forms.FlaggedTaskForm({'text': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'reply': 'truthy', 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        ok_(not self.task.resolved, 'The task should not automatically resolve when replying.')
        mock_reply.assert_called_with(test_text)

    def test_post_reply_resolve(self, mock_reply):
        """The task should optionally resolve when replying"""
        test_text = 'Lorem ipsum'
        form = task.forms.FlaggedTaskForm({'text': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'reply': 'truthy', 'resolve': True, 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        ok_(self.task.resolved, 'The task should resolve.')
        mock_reply.assert_called_with(test_text)

@mock.patch('muckrock.task.models.ProjectReviewTask.reply')
class ProjectReviewTaskViewTests(TestCase):
    """Tests FlaggedTask POST handlers"""
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True)
        self.url = reverse('projectreview-task-list')
        self.view = task.views.ProjectReviewTaskList.as_view()
        self.task = task.factories.ProjectReviewTaskFactory()
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
        form = task.forms.ProjectReviewTaskForm({'reply': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'action': 'reply', 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        ok_(not self.task.resolved, 'The task should not automatically resolve when replying.')
        mock_reply.assert_called_with(test_text)

    def test_post_reply_approve(self, mock_reply):
        """The task should optionally resolve when replying"""
        test_text = 'Lorem ipsum'
        form = task.forms.ProjectReviewTaskForm({'reply': test_text})
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
        form = task.forms.ProjectReviewTaskForm({'reply': test_text})
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'action': 'reject', 'task': self.task.pk})
        self.post_request(post_data)
        self.task.refresh_from_db()
        self.task.project.refresh_from_db()
        ok_(self.task.project.private, 'The project should be made private.')
        ok_(self.task.resolved, 'The task should be resolved.')
        mock_reply.assert_called_with(test_text, 'rejected')


class StaleAgencyTaskViewTests(TestCase):
    """Tests StaleAgencyTask POST handlers"""
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True)
        self.url = reverse('stale-agency-task-list')
        self.view = task.views.StaleAgencyTaskList.as_view()
        self.task = StaleAgencyTaskFactory()
        self.request_factory = RequestFactory()

    def test_get_single(self):
        """Should be able to view a single task"""
        _url = reverse('stale-agency-task', kwargs={'pk': self.task.pk})
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

    @mock.patch('muckrock.task.models.StaleAgencyTask.update_email')
    def test_post_email_update(self, mock_update):
        """Should update email when given an email and a list of FOIA"""
        new_email = u'new_email@muckrock.com'
        foia = factories.FOIARequestFactory()
        post_data = {
            'email': new_email,
            'foia': [foia.pk],
            'update': 'truthy',
            'resolve': 'truthy',
            'task': self.task.pk
        }
        self.post_request(post_data)
        self.task.refresh_from_db()
        self.task.agency.refresh_from_db()
        ok_(mock_update.called, 'The email should be updated.')
        ok_(self.task.resolved, 'The task should resolve.')
        ok_(not self.task.agency.stale, 'The agency should no longer be stale.')

    @mock.patch('muckrock.task.models.StaleAgencyTask.update_email')
    def test_post_bad_email_update(self, mock_update):
        """An invalid email should be prevented from updating or resolving anything."""
        bad_email = u'bad_email'
        foia = factories.FOIARequestFactory()
        post_data = {
            'email': bad_email,
            'foia': [foia.pk],
            'update': 'truthy',
            'resolve': 'truthy',
            'task': self.task.pk
        }
        self.post_request(post_data)
        self.task.refresh_from_db()
        self.task.agency.refresh_from_db()
        ok_(not mock_update.called, 'The email should not be updated.')
        ok_(not self.task.resolved, 'The task should not resolve.')
        ok_(self.task.agency.stale, 'The agency should still be stale.')

    @mock.patch('muckrock.task.models.StaleAgencyTask.update_email')
    def test_post_bad_foia(self, mock_update):
        """An invalid FOIA should not prevent the task from updating or resolving anything."""
        new_email = u'new_email@muckrock.com'
        foia = factories.FOIARequestFactory()
        bad_pk = 12345
        post_data = {
            'email': new_email,
            'foia': [foia.pk, bad_pk],
            'update': 'truthy',
            'resolve': 'truthy',
            'task': self.task.pk
        }
        self.post_request(post_data)
        self.task.refresh_from_db()
        self.task.agency.refresh_from_db()
        ok_(mock_update.called, 'The email should be updated.')
        ok_(self.task.resolved, 'The task should resolve.')
        ok_(not self.task.agency.stale, 'The agency should no longer be stale.')


@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class NewAgencyTaskViewTests(TestCase):
    """Tests NewAgencyTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('new-agency-task-list')
        self.task = task.models.NewAgencyTask.objects.get(pk=7)
        self.task.agency.status = 'pending'
        self.task.agency.save()
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_get_single(self):
        """Should be able to view a single task"""
        response = self.client.get(reverse('new-agency-task', kwargs={'pk': self.task.pk}))
        eq_(response.status_code, 200)

    def test_post_accept(self):
        contact_data = {
            'name': 'Test Agency',
            'address': '1234 Whatever Street',
            'email': 'who.cares@whatever.com'
        }
        form = agency.forms.AgencyForm(contact_data, instance=self.task.agency)
        ok_(form.is_valid())
        post_data = form.cleaned_data
        post_data.update({'approve': 'truthy', 'task': self.task.pk})
        self.client.post(self.url, post_data)
        updated_task = task.models.NewAgencyTask.objects.get(pk=self.task.pk)
        eq_(updated_task.agency.status, 'approved',
                ('New agency task should approve agency when'
                ' given a truthy value for the "approve" field'))
        eq_(updated_task.resolved, True,
                ('New agency task should resolve when given any'
                ' truthy value for the "approve" data field'))

    def test_post_reject(self):
        """Rejecting the agency requires a replacement agency"""
        replacement = agency.models.Agency.objects.get(id=2)
        self.client.post(self.url, {
            'reject': 'truthy',
            'task': self.task.id,
            'replacement': replacement.id
        })
        updated_task = task.models.NewAgencyTask.objects.get(pk=self.task.id)
        eq_(updated_task.agency.status, 'rejected',
                ('New agency task should not approve the agency'
                ' when given a truthy value for the "reject" field'))
        eq_(updated_task.resolved, True,
                ('New agency task should resolve when given any'
                ' truthy value for the "reject" data field'))

@mock.patch('muckrock.message.notifications.SlackNotification.send', mock_send)
class ResponseTaskListViewTests(TestCase):
    """Tests ResponseTask-specific POST handlers"""
    def setUp(self):
        self.user = factories.UserFactory(is_staff=True)
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
            'task': self.task.pk
        }
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        foia.refresh_from_db()
        eq_(foia.price, float(price), 'The price on the FOIA should be set.')
        ok_(self.task.resolved, 'Setting the price should resolve the task.')

    def test_post_set_status(self):
        """Setting the status should save it to the response and request, then resolve task."""
        status_change = 'done'
        data = {'status': status_change, 'set_foia': True, 'task': self.task.pk}
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        self.task.communication.foia.refresh_from_db()
        comm_status = self.task.communication.status
        foia_status = self.task.communication.foia.status
        eq_(comm_status, status_change,
            'The status change should be saved to the communication.')
        eq_(foia_status, status_change,
            'The status of the FOIA should be set.')
        eq_(self.task.resolved, True,
            'Setting the status should resolve the task')

    def test_post_set_comm_status(self):
        """Setting the status on just the communication should not influence its request."""
        status_change = 'done'
        existing_foia_status = self.task.communication.foia.status
        data = {'status': status_change, 'set_foia': False, 'task': self.task.pk}
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        self.task.communication.foia.refresh_from_db()
        comm_status = self.task.communication.status
        foia_status = self.task.communication.foia.status
        eq_(comm_status, status_change,
            'The status change should be saved to the communication.')
        eq_(foia_status, existing_foia_status,
            'The status of the FOIA should not be changed.')
        eq_(self.task.resolved, True,
            'Settings the status should resolve the task.')

    def test_post_tracking_number(self):
        """Setting the tracking number should save it to the response's request."""
        new_tracking_id = 'ABC123OMGWTF'
        data = {
            'tracking_number': new_tracking_id,
            'status': 'done',
            'task': self.task.pk
        }
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        self.task.communication.foia.refresh_from_db()
        foia_tracking = self.task.communication.foia.tracking_id
        eq_(foia_tracking, new_tracking_id,
            'The new tracking number should be saved to the associated request.')
        ok_(self.task.resolved,
            'Setting the tracking number should resolve the task')

    def test_post_move(self):
        """Moving the response should save it to a new request."""
        other_foia = factories.FOIARequestFactory()
        starting_date = self.task.communication.date
        data = {'move': other_foia.id, 'status': 'done', 'task': self.task.pk}
        http_post_response(self.url, self.view, data, self.user)
        self.task.refresh_from_db()
        self.task.communication.refresh_from_db()
        ending_date = self.task.communication.date
        eq_(self.task.communication.foia, other_foia,
            'The response should be moved to a different FOIA.')
        ok_(self.task.resolved,
            'Moving the status should resolve the task')
        eq_(starting_date, ending_date,
            'Moving the communication should not change its date.')

    def test_post_move_multiple(self):
        """Moving the response to multiple requests modify all the requests."""
        other_foias = [
            factories.FOIARequestFactory(),
            factories.FOIARequestFactory(),
            factories.FOIARequestFactory()
        ]
        move_to_ids = ', '.join([str(foia.id) for foia in other_foias])
        change_status = 'done'
        change_tracking = 'DEADBEEF'
        data = {
            'move': move_to_ids,
            'status': change_status,
            'tracking_number': change_tracking,
            'task': self.task.pk
        }
        http_post_response(self.url, self.view, data, self.user)
        for foia in other_foias:
            foia.refresh_from_db()
            eq_(change_tracking, foia.tracking_id,
              'Tracking should update for each request in move list.')

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
        save_foia_comm(foia, foia.user, 'Just testing, u no', foia.user)
        eq_(foia.communications.count(), num_comms + 1,
            'Should add a new communication to the FOIA.')
        num_comms = foia.communications.count()
        # next try resolving the task with a tracking number set
        data = {
            'resolve': 'true',
            'tracking_number': u'12345',
            'task': self.task.pk
        }
        http_post_response(self.url, self.view, data, self.user)
        foia.refresh_from_db()
        eq_(foia.communications.count(), num_comms,
            'The number of communications should not have changed from before.')
