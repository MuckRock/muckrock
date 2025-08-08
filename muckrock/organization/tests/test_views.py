"""
Test organization views
"""

# Django
from django.test import Client, TestCase
from django.urls import reverse

# MuckRock
from muckrock.organization.factories import OrganizationFactory


class OrganizationViewsTests(TestCase):
    """Test the views for the organization app"""

    def setUp(self):
        """Set up models for the organization"""
        self.org = OrganizationFactory()
        self.client = Client()

    def test_index(self):
        """The index should redirect"""
        response = self.client.get(reverse("org-index"))
        assert response.status_code == 200

    def test_detail(self):
        """Detail page should redirect"""
        response = self.client.get(self.org.get_absolute_url())
        assert response.status_code == 200
