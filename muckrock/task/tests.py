"""
Tests for Tasks app
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mock import Mock, patch
import nose.tools as nose

class TaskListViewTests(TestCase):
    """Test that the task list view resolves and renders correctly."""

    fixtures = ['test_users.json']

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
