"""
Test organization views
"""

# Django
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

# Third Party
from nose.tools import eq_

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
        response = self.client.get(reverse('org-index'))
        eq_(response.status_code, 200)

    def test_detail(self):
        """Detail page should redirect"""
        response = self.client.get(self.org.get_absolute_url())
        eq_(response.status_code, 200)
