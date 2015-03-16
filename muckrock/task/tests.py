"""
Tests for Tasks app
"""

from django.test import TestCase
from django.core.urlresolvers import reverse

from mock import Mock, patch
import nose.tools as nose

class TaskListViewTests(TestCase):
    """Test that the task list view resolves and renders correctly."""

    def setUp(self):
        self.url = reverse('task-list')

    def test_url(self):
        nose.eq_(self.url, '/task/',
            'The task list should be the base task URL')
