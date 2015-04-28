"""
Tests for Tasks views
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

import logging
import nose.tools as nose

from muckrock import task
from muckrock import agency
from muckrock.foia.models import FOIARequest
from muckrock.views import MRFilterableListView

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
        nose.eq_(self.url, '/task/',
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
        nose.eq_(response.status_code, 200,
            ('Should respond to staff requests for task list page with 200.'
            ' Actually responds with %d' % response.status_code))

    def test_class_inheritance(self):
        # pylint: disable=no-self-use
        actual = task.views.TaskList.__bases__
        expected = MRFilterableListView().__class__
        nose.ok_(expected in actual,
            'Task list should inherit from MRFilterableListView class')

    def test_render_task_list(self):
        """The list should have rendered task widgets in its object_list context variable"""
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        obj_list = response.context['object_list']
        nose.ok_(obj_list,
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
        nose.eq_(updated_task.resolved, True,
            'Tasks should be resolved by posting the task ID with a "resolve" request.')
        nose.eq_(updated_task.resolved_by, user,
            'Task should record the logged in user who resolved it.')


    def test_post_do_not_resolve_task(self):
        self.client.post(self.url, {'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        print updated_task.resolved
        nose.eq_(updated_task.resolved, False,
            'Tasks should not be resolved when no "resolve" data is POSTed.')

    def test_post_assign_task(self):
        # the PK for 'adam' is 1
        self.client.post(self.url, {'assign': 1, 'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.assigned.pk, 1,
            'Tasks should be assigned by posting the task ID and user ID with an "assign" request.')

    def test_bad_assign(self):
        # there is no user with a PK of 99
        response = self.client.post(self.url, {'assign': 99, 'task': self.task.pk})
        nose.eq_(response.status_code, 404)

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
            nose.eq_(updated_task.resolved, True,
                'Task %d should be resolved when doing a batched resolve' % updated_task.pk)

    def test_batch_assign_tasks(self):
        self.client.post(self.url, {'assign': 1, 'tasks': [1, 2, 3]})
        updated_tasks = [task.models.Task.objects.get(pk=t.pk) for t in self.tasks]
        for updated_task in updated_tasks:
            nose.eq_(updated_task.assigned.pk, 1,
                'Task %d should be assigned when doing a batched assign' % updated_task.pk)

class OrphanTaskViewTests(TestCase):
    """Tests OrphanTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.task = task.models.OrphanTask.objects.get(pk=2)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_move(self):
        foia_1_comm_count = FOIARequest.objects.get(pk=1).communications.all().count()
        foia_2_comm_count = FOIARequest.objects.get(pk=2).communications.all().count()
        self.client.post(self.url, {'move': '1, 2', 'task': self.task.pk})
        updated_foia_1_comm_count = FOIARequest.objects.get(pk=1).communications.all().count()
        updated_foia_2_comm_count = FOIARequest.objects.get(pk=2).communications.all().count()
        updated_task = task.models.OrphanTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Orphan task should be moved by posting the FOIA pks and task ID.')
        nose.eq_(updated_foia_1_comm_count, foia_1_comm_count + 1,
            'Communication should be added to FOIA')
        nose.eq_(updated_foia_2_comm_count, foia_2_comm_count + 1,
            'Communication should be added to FOIA')

    def test_reject(self):
        self.client.post(self.url, {'reject': True, 'task': self.task.pk})
        updated_task = task.models.OrphanTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
                ('Orphan task should be rejected by posting any'
                ' truthy value to the "reject" parameter and task ID.'))

    def test_reject_despite_likely_foia(self):
        likely_foia_pk = self.task.communication.likely_foia.pk
        likely_foia = FOIARequest.objects.get(pk=likely_foia_pk)
        likely_foia_comm_count = likely_foia.communications.all().count()
        nose.ok_(likely_foia_pk,
                'Communication should have a likely FOIA for this test')
        self.client.post(self.url, {
            'move': str(likely_foia_pk),
            'reject': 'true',
            'task': self.task.pk})
        updated_likely_foia_comm_count = likely_foia.communications.all().count()
        nose.eq_(likely_foia_comm_count, updated_likely_foia_comm_count,
                ('Rejecting an orphan with a likely FOIA should not move'
                ' the communication to that FOIA'))

class TaskListViewSnailMailTaskPOSTTests(TestCase):
    """Tests SnailMailTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.task = task.models.SnailMailTask.objects.get(pk=3)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_post_set_status(self):
        self.client.post(self.url, {'status': 'ack', 'task': self.task.pk})
        updated_task = task.models.SnailMailTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Snail mail task should resolve itself when setting status of its communication')

class NewAgencyTaskViewTests(TestCase):
    """Tests NewAgencyTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.task = task.models.NewAgencyTask.objects.get(pk=7)
        self.task.agency.approved = False
        self.task.agency.save()
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_post_accept(self):
        form = agency.forms.AgencyForm(instance=self.task.agency)
        logging.debug(form.is_valid())
        logging.debug(form.errors)
        logging.debug(form)
        nose.ok_(form.is_valid())
        self.client.post(self.url, {'approve': 'truthy', 'agency_form': form.data, 'task': self.task.pk})
        updated_task = task.models.NewAgencyTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.agency.approved, True,
                ('New agency task should approve agency when'
                ' given a truthy value for the "approve" field'))
        nose.eq_(updated_task.resolved, True,
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
        nose.eq_(updated_task.agency.approved, False,
                ('New agency task should not approve the agency'
                ' when given a truthy value for the "reject" field'))
        nose.eq_(updated_task.resolved, True,
                ('New agency task should resolve when given any'
                ' truthy value for the "reject" data field'))

class TaskListViewResponseTaskPOSTTests(TestCase):
    """Tests ResponseTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.task = task.models.ResponseTask.objects.get(pk=8)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_post_set_status(self):
        self.client.post(self.url, {'status': 'done', 'task': self.task.pk})
        updated_task = task.models.ResponseTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Setting the status should resolve the task')
