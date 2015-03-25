"""
Tests for Tasks views
"""

from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase, Client

import nose.tools as nose

from muckrock import task
from muckrock.views import MRFilterableListView

# pylint: disable=missing-docstring

class TaskListViewTests(TestCase):
    """Test that the task list view resolves and renders correctly."""

    fixtures = ['test_users.json']

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
        response = self.client.post(self.url, {'resolve': True, 'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Tasks should be resolved by posting the task ID with a "resolve" request.')

    def test_post_do_not_resolve_task(self):
        response = self.client.post(self.url, {'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        print updated_task.resolved
        nose.eq_(updated_task.resolved, False,
            'Tasks should not be resolved when no "resolve" data is POSTed.')

    def test_post_assign_task(self):
        # the PK for 'adam' is 1
        response = self.client.post(self.url, {'assign': 1, 'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.assigned.pk, 1,
            'Tasks should be assigned by posting the task ID and user ID with an "assign" request.')

    def test_post_assign_task_to_nonexistant_user(self):
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
        response = self.client.post(self.url, {'resolve': 'true', 'tasks': [1, 2, 3]})
        updated_tasks = [task.models.Task.objects.get(pk=t.pk) for t in self.tasks]
        for updated_task in updated_tasks:
            nose.eq_(updated_task.resolved, True,
                'Task %d should be resolved when doing a batched resolve' % updated_task.pk)

    def test_batch_assign_tasks(self):
        response = self.client.post(self.url, {'assign': 1, 'tasks': [1, 2, 3]})
        updated_tasks = [task.models.Task.objects.get(pk=t.pk) for t in self.tasks]
        for updated_task in updated_tasks:
            nose.eq_(updated_task.assigned.pk, 1,
                'Task %d should be assigned when doing a batched assign' % updated_task.pk)

class TaskListViewOrphanTaskPOSTTests(TestCase):
    """Tests OrphanTask-specific POST handlers"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json', 'test_task.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.task = task.models.OrphanTask.objects.get(pk=2)
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_post_move_orphan_task_to_foias(self):
        response = self.client.post(self.url, {'move': '1, 2', 'task': self.task.pk})
        updated_task = task.models.OrphanTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Orphan task should be moved by posting the FOIA pks and task ID.')

    def test_post_reject_orphan_task(self):
        response = self.client.post(self.url, {'reject': True, 'task': self.task.pk})
        updated_task = task.models.OrphanTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Orphan task should be rejected by posting any truthy value to the "reject" parameter and task ID.')

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
        response = self.client.post(self.url, {'status': 'ack', 'task': self.task.pk})
        updated_task = task.models.SnailMailTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Snail mail task should resolve itself when setting status of its communication')

class TaskListViewNewAgencyTaskPOSTTests(TestCase):
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
        response = self.client.post(self.url, {'approve': 'truthy', 'task': self.task.pk})
        updated_task = task.models.NewAgencyTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.agency.approved, True,
            'New agency task should approve agency when given a truthy value for the "approve" field')
        nose.eq_(updated_task.resolved, True,
            'New agency task should resolve when given any truthy value for the "approve" data field')

    def test_post_reject(self):
        response = self.client.post(self.url, {'reject': 'truthy', 'task': self.task.pk})
        updated_task = task.models.NewAgencyTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.agency.approved, False,
            'New agency task should not approve the agency when given a truthy value for the "reject" field')
        nose.eq_(updated_task.resolved, True,
            'New agency task should resolve when given any truthy value for the "reject" data field')

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
        response = self.client.post(self.url, {'status': 'done', 'task': self.task.pk})
        updated_task = task.models.ResponseTask.objects.get(pk=self.task.pk)
        nose.eq_(updated_task.resolved, True,
            'Setting the status should resolve the task')
