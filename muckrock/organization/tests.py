"""
Tests for the organization application
"""

from django.contrib.auth.models import User
from django.test import TestCase

from datetime import datetime

from muckrock.organization.models import Organization

class OrganizationURLTests(TestCase):
    """Test the views for the organization app"""

    def setUp(self):
        """Set up models for the organization"""
        owner = User.objects.create(
            username='TestOwner',
            password='testowner'
        )
        Organization.objects.create(
            name='Test Organization',
            slug='test-organization',
            owner=owner,
            date_update=datetime.now(),
        )

    def test_index(self):
        """The index should be OK"""
        response = self.client.get('/organization/')
        self.assertEqual(response.status_code, 200)

    def test_create(self):
        """Create should redirect"""
        response = self.client.get('/organization/create/')
        self.assertEqual(response.status_code, 302)

    def test_detail(self):
        """Detail page should be OK"""
        response = self.client.get('/organization/test-organization/')
        self.assertEqual(response.status_code, 200)

    def test_delete(self):
        """ordinary users should not be able to access the delete page, hence 404"""
        response = self.client.get('/organization/test-orgainzation/delete/')
        self.assertEqual(response.status_code, 404)
