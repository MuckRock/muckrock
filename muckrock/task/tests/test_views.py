"""
Tests for Tasks views
"""
from datetime import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

import nose

from muckrock import task
from muckrock import agency
from muckrock.foia.models import FOIARequest
from muckrock.foia.views import save_foia_comm
from muckrock.views import MRFilterableListView

eq_ = nose.tools.eq_
ok_ = nose.tools.ok_
raises = nose.tools.raises

# pylint: disable=missing-docstring

class TaskListViewTests(TestCase):
    """Test that the task list view resolves and renders correctly."""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.client = Client()
        self.task = task.models.Task.objects.create()

    def test_url(self):
        eq_(self.url, '/task/',
            'The task list should be the base task URL')

    def test_login_required(self):
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/accounts/login/?next=%s' % self.url)

    def test_not_staff_not_ok(self):
        self.client.login(username='bob', password='abc')
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/accounts/login/?next=%s' % self.url)

    def test_staff_ok(self):
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        eq_(response.status_code, 200,
            ('Should respond to staff requests for task list page with 200.'
            ' Actually responds with %d' % response.status_code))

    def test_class_inheritance(self):
        # pylint: disable=no-self-use
        actual = task.views.TaskList.__bases__
        expected = MRFilterableListView().__class__
        ok_(expected in actual,
            'Task list should inherit from MRFilterableListView class')

    def test_render_task_list(self):
        """The list should have rendered task widgets in its object_list context variable"""
        # pylint: disable=no-member
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        obj_list = response.context['object_list']
        ok_(obj_list,
            'Object list should not be empty.')

class TaskListViewPOSTTests(TestCase):
    """Tests POST requests to the Task list view"""
    # we have to get the task again if we want to see the updated value

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.task = task.models.Task.objects.get(pk=1)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_post_resolve_task(self):
        self.client.post(self.url, {'resolve': True, 'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        user = User.objects.get(username='adam')
        eq_(updated_task.resolved, True,
            'Tasks should be resolved by posting the task ID with a "resolve" request.')
        eq_(updated_task.resolved_by, user,
            'Task should record the logged in user who resolved it.')

    def test_post_do_not_resolve_task(self):
        self.client.post(self.url, {'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        eq_(updated_task.resolved, False,
            'Tasks should not be resolved when no "resolve" data is POSTed.')

class TaskListViewBatchedPOSTTests(TestCase):
    """Tests batched POST requests for all tasks"""
    # we have to get the task again if we want to see the updated value

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        task1 = task.models.Task.objects.get(pk=1)
        task2 = task.models.Task.objects.get(pk=2)
        task3 = task.models.Task.objects.get(pk=3)
        self.tasks = [task1, task2, task3]
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_batch_resolve_tasks(self):
        self.client.post(self.url, {'resolve': 'true', 'tasks': [1, 2, 3]})
        updated_tasks = [task.models.Task.objects.get(pk=t.pk) for t in self.tasks]
        for updated_task in updated_tasks:
            eq_(updated_task.resolved, True,
                'Task %d should be resolved when doing a batched resolve' % updated_task.pk)

class OrphanTaskViewTests(TestCase):
    """Tests OrphanTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('orphan-task-list')
        self.task = task.models.OrphanTask.objects.get(pk=2)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_move(self):
        foia_1_comm_count = FOIARequest.objects.get(pk=1).communications.all().count()
        foia_2_comm_count = FOIARequest.objects.get(pk=2).communications.all().count()
        starting_date = self.task.communication.date
        self.client.post(self.url, {'move': '1, 2', 'task': self.task.pk})
        updated_foia_1_comm_count = FOIARequest.objects.get(pk=1).communications.all().count()
        updated_foia_2_comm_count = FOIARequest.objects.get(pk=2).communications.all().count()
        updated_task = task.models.OrphanTask.objects.get(pk=self.task.pk)
        ending_date = updated_task.communication.date
        eq_(updated_task.resolved, True,
            'Orphan task should be moved by posting the FOIA pks and task ID.')
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
        self.task.communication.priv_from_who = 'Michael Morisy <michael@muckrock.com>'
        self.task.communication.save()
        self.client.post(self.url, {
            'reject': 'true',
            'blacklist': True,
            'task': self.task.pk})
        ok_(task.models.BlacklistDomain.objects.filter(domain='muckrock.com'))

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

    def test_post_set_status(self):
        """Should update the status of the task's communication and associated request."""
        new_status = 'ack'
        self.client.post(self.url, {'status': new_status, 'task': self.task.pk})
        updated_task = task.models.SnailMailTask.objects.get(pk=self.task.pk)
        eq_(updated_task.communication.status, new_status,
            'Should update status of the communication.')
        eq_(updated_task.communication.foia.status, new_status,
            'Should update the status of the communication\'s associated request.')

    def test_post_update_date(self):
        """Should update the date of the communication to today."""
        comm_date = self.task.communication.date
        self.client.post(self.url, {'status': 'ack', 'update_date': 'true', 'task': self.task.pk})
        updated_task = task.models.SnailMailTask.objects.get(pk=self.task.pk)
        ok_(updated_task.communication.date > comm_date,
            'Should update the communication date.')
        eq_(updated_task.communication.date.day, datetime.now().day,
            'Should update the communication to today\'s date.')

class NewAgencyTaskViewTests(TestCase):
    """Tests NewAgencyTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('new-agency-task-list')
        self.task = task.models.NewAgencyTask.objects.get(pk=7)
        self.task.agency.approved = False
        self.task.agency.save()
        self.client = Client()
        self.client.login(username='adam', password='abc')

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
        eq_(updated_task.agency.approved, True,
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
        eq_(updated_task.agency.approved, False,
                ('New agency task should not approve the agency'
                ' when given a truthy value for the "reject" field'))
        eq_(updated_task.resolved, True,
                ('New agency task should resolve when given any'
                ' truthy value for the "reject" data field'))

class ResponseTaskListViewTests(TestCase):
    """Tests ResponseTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('response-task-list')
        self.task = task.models.ResponseTask.objects.get(pk=8)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_post_set_price(self):
        """Setting the price should update the price on the response's request."""
        price = 1
        self.client.post(self.url, {
            'status': 'done',
            'price': price,
            'task': self.task.pk
        })
        updated_task = task.models.ResponseTask.objects.get(pk=self.task.pk)
        foia_price = updated_task.communication.foia.price
        eq_(foia_price, float(price), 'The price on the FOIA should be set.')
        ok_(updated_task.resolved, 'Setting the price should resolve the task.')

    def test_post_set_status(self):
        """Setting the status should save it to the response and request, then resolve task."""
        status_change = 'done'
        self.client.post(self.url, {'status': status_change, 'task': self.task.pk})
        updated_task = task.models.ResponseTask.objects.get(pk=self.task.pk)
        comm_status = updated_task.communication.status
        foia_status = updated_task.communication.foia.status
        eq_(comm_status, status_change,
            'The status change should be saved to the communication.')
        eq_(foia_status, status_change,
            'The status of the FOIA should be set.')
        eq_(updated_task.resolved, True,
            'Setting the status should resolve the task')

    def test_post_tracking_number(self):
        """Setting the tracking number should save it to the response's request."""
        new_tracking_id = 'ABC123OMGWTF'
        self.client.post(self.url, {
            'tracking_number': new_tracking_id,
            'status': 'done',
            'task': self.task.pk
        })
        updated_task = task.models.ResponseTask.objects.get(pk=self.task.pk)
        foia_tracking = updated_task.communication.foia.tracking_id
        eq_(foia_tracking, new_tracking_id,
            'The new tracking number should be saved to the associated request.')
        ok_(updated_task.resolved,
            'Setting the tracking number should resolve the task')

    def test_post_move(self):
        """Moving the response should save it to a new request."""
        move_to_id = 2
        starting_date = self.task.communication.date
        self.client.post(self.url, {'move': move_to_id, 'status': 'done', 'task': self.task.pk})
        updated_task = task.models.ResponseTask.objects.get(pk=self.task.pk)
        foia_id = updated_task.communication.foia.id
        ending_date = updated_task.communication.date
        eq_(foia_id, move_to_id,
            'The response should be moved to a different FOIA.')
        ok_(updated_task.resolved,
            'Moving the status should resolve the task')
        eq_(starting_date, ending_date,
            'Moving the communication should not change its date.')

    def test_post_move_multiple(self):
        """Moving the response to multiple requests should only modify the first request."""
        move_to_ids = '2, 3, 4'
        change_status = 'done'
        change_tracking = 'DEADBEEF'
        self.client.post(self.url, {
            'move': move_to_ids,
            'status': change_status,
            'tracking_number': change_tracking,
            'task': self.task.pk
        })
        foia2 = FOIARequest.objects.get(pk=2)
        foia3 = FOIARequest.objects.get(pk=3)
        foia4 = FOIARequest.objects.get(pk=4)
        # foia 2 should get updated status, tracking number
        # foia 3 & 4 should stay just the way they are
        eq_(change_tracking, foia2.tracking_id,
            'Tracking should update for first request in move list.')
        ok_(change_tracking is not foia3.tracking_id and change_tracking is not foia4.tracking_id,
            'Tracking should not update for subsequent requests in list.')

    def test_terrible_data(self):
        """Posting awful data shouldn't cause everything to collapse."""
        response = self.client.post(self.url, {
            'move': 'omglol, howru',
            'status': 'notastatus',
            'tracking_number': ['wtf'],
            'task': self.task.pk
        })
        ok_(response)

    def test_foia_integrity(self):
        """
        Updating a request through a task should maintain integrity of that request's data.
        This is in response to issue #387.
        """
        # first saving a comm
        foia = self.task.communication.foia
        num_comms = foia.communications.count()
        save_foia_comm(foia, 'Testman', 'Just testing, u no')
        eq_(foia.communications.count(), num_comms + 1,
            'Should add a new communication to the FOIA.')
        num_comms = foia.communications.count()
        # next try resolving the task with a tracking number set
        self.client.post(self.url, {
            'resolve': 'true',
            'tracking_number': u'12345',
            'task': self.task.pk
        })
        eq_(foia.communications.count(), num_comms,
            'The number of communications should not have changed from before.')
