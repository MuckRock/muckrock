"""
Tests for Tasks models
"""

from django.contrib.auth.models import User
from django.test import TestCase

from datetime import datetime
import nose.tools as nose

from muckrock import task
from muckrock.foia.models import FOIACommunication

# pylint: disable=missing-docstring

class TaskTests(TestCase):
    """Test the Task base class"""

    fixtures = ['test_users.json']

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

    def test_assign(self):
        user = User.objects.get(pk=1)
        self.task.assign(user)
        nose.ok_(self.task.assigned is user,
            'Should assign the task to the specified user')

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
