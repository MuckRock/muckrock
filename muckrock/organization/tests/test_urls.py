"""
Test organization urls
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client

from muckrock.organization.models import Organization

from datetime import datetime
from mock import Mock, patch
from nose.tools import eq_

class OrganizationURLTests(TestCase):
    """Test the urls for the organization app"""

    def setUp(self):
        """Set up models for the organization"""
        owner = Mock(spec=User)
        org = Mock(spec=Organization)
        self.client = Client()

    def test_index(self):
        """The index should be OK"""
        response = self.client.get('/organization/')
        eq_(response.status_code, 200)

    def test_create(self):
        """Create should redirect"""
        response = self.client.get('/organization/create/')
        eq_(response.status_code, 302)

    def test_detail(self):
        """Detail page should be OK"""
        response = self.client.get('/organization/test-organization/')
        eq_(response.status_code, 200)

    def test_delete(self):
        """ordinary users should not be able to access the delete page, hence 404"""
        response = self.client.get('/organization/test-orgainzation/delete/')
        eq_(response.status_code, 404)
