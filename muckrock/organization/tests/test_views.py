"""
Test organization views
"""

# Django
from django.test import Client, TestCase
from django.urls import reverse

# Standard Library
from uuid import uuid4

# MuckRock
from muckrock.core.factories import UserFactory
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

    def test_an_org_uuid_redirects_to_the_org(self):
        """The UUID resolves to the organization's page"""
        response = self.client.get(reverse("org-uuid", kwargs={"uuid": self.org.uuid}))
        assert response.status_code == 302
        assert response.url == self.org.get_absolute_url()

    def test_an_individual_org_uuid_redirects_to_its_user(self):
        """Individual orgs have no page, so they go to their user's profile"""
        user = UserFactory()
        organization = user.profile.individual_organization
        response = self.client.get(
            reverse("org-uuid", kwargs={"uuid": organization.uuid})
        )
        assert response.status_code == 302
        assert response.url == user.profile.get_absolute_url()

    def test_an_unknown_org_uuid_is_a_404(self):
        """A UUID with no organization is not found"""
        response = self.client.get(reverse("org-uuid", kwargs={"uuid": uuid4()}))
        assert response.status_code == 404
