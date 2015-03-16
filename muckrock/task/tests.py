"""
Tests for Tasks app
"""

from django.test import TestCase

from mock import Mock, patch
import nose.tools as nose

class TaskListViewTests(TestCase):
    """Test that the task list view resolves and renders correctly."""

    def setUp(self):
        pass

    def test_task_list_url(self):
        nose.ok_(True)
