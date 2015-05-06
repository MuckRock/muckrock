"""
Tests the Task templatetags
"""

from django.test import TestCase
import logging
from muckrock.task.models import Task
from muckrock.task.templatetags import tasks as task_tags
import nose

ok_ = nose.tools.ok_

class TaskTagsFunctionalTests(TestCase):
    """Everything about the template tags should be sound and stable."""

    def setUp(self):
        self.task = Task.objects.create()

    def test_basic_tag(self):
        """The basic tag should render without issue."""
        ok_(task_tags.task(self.task))
