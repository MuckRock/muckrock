"""
Tests for Tasks views
"""

from django.test import TestCase, Client
from django.core.urlresolvers import reverse

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

    fixtures = ['test_users.json']

    def setUp(self):
        self.url = reverse('task-list')
        self.task = task.models.Task.objects.create()
        self.client = Client()
        self.client.login(username='adam', password='abc')

    def test_post_resolve_task(self):
        response = self.client.post(self.url, {'resolve': True, 'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        nose.ok_(updated_task.resolved is True,
            'Tasks should be resolved by posting the task ID with a "resolve" request.')

    def test_post_do_not_resolve_task(self):
        response = self.client.post(self.url, {'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        print updated_task.resolved
        nose.ok_(updated_task.resolved is not True,
            'Tasks should not be resolved when no "resolve" data is POSTed.')

    def test_post_assign_task(self):
        # the PK for 'adam' is 1
        response = self.client.post(self.url, {'assign': 1, 'task': self.task.pk})
        updated_task = task.models.Task.objects.get(pk=self.task.pk)
        nose.ok_(updated_task.assigned.pk is 1,
            'Tasks should be assigned by posting the task ID and user ID with an "assign" request.')
