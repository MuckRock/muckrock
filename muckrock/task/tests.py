"""
Tests for Tasks app
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from datetime import datetime
import nose.tools as nose

from muckrock import task
from muckrock.foia.models import FOIACommunication
from muckrock.views import MRFilterableListView

class TaskTests(TestCase):
    """Test the Task base class"""

    def setUp(self):
        self.task = task.models.Task.objects.create()

    def test_task_creates_successfully(self):
        nose.ok_(self.task,
            'Tasks given no arguments should create successfully')

    def test_unicode(self):
        nose.eq_(str(self.task), 'Task: %d' % self.task.pk,
            'Unicode string should return the classname and PK of the task')

    def test_resolve(self):
        self.task.resolve()
        nose.ok_(self.task.resolved is True,
            'Resolving task should set resolved field to True')
        nose.ok_(self.task.date_done is not None,
            'Resolving task should set date_done')

class OrphanTaskTests(TestCase):
    """Test the OrphanTask class"""

    def setUp(self):
        self.comm = FOIACommunication.objects.create(date=datetime.now(), from_who='God')
        self.task = task.models.OrphanTask.objects.create(
            reason='ib',
            communication=self.comm,
            address='Whatever Who Cares')

    def test_task_creates_successfully(self):
        nose.ok_(self.task,
            'Orphan tasks given reason and communication arguments should create successfully')

class TaskListViewTests(TestCase):
    """Test that the task list view resolves and renders correctly."""

    fixtures = ['test_users.json', ]

    def setUp(self):
        self.url = reverse('task-list')
        self.client = Client()

    def test_url(self):
        nose.eq_(self.url, '/task/',
            'The task list should be the base task URL')

    def test_login_required(self):
        response = self.client.get(self.url, follow=True)
        print(response.status_code)
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

    def test_inherits_from_MRFilterableListView(self):
        actual = task.views.TaskList.__bases__
        expected = MRFilterableListView().__class__
        nose.ok_(expected in actual,
            'Task list should inherit from MRFilterableListView class')
