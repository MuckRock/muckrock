"""
Test organization urls
"""

# Django
from django.test import Client, TestCase

# Third Party
from nose.tools import eq_

# MuckRock
import muckrock.factories


class OrganizationURLTests(TestCase):
    """Test the urls for the organization app"""

    def setUp(self):
        """Set up models for the organization"""
        self.org = muckrock.factories.OrganizationFactory()
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
        response = self.client.get(self.org.get_absolute_url())
        eq_(response.status_code, 200)

    def test_delete(self):
        """ordinary users should not be able to access the delete page, hence 404"""
        response = self.client.get(self.org.get_absolute_url() + '/delete/')
        eq_(response.status_code, 404)
