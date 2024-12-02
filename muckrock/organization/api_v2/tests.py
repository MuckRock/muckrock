""" Tests for the organization viewsets """

# Django
from django.test import Client, TestCase
from django.urls import reverse

# Third Party
from rest_framework import status

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.organization.factories import OrganizationFactory


# pylint: disable=too-many-instance-attributes
class OrganizationViewSetTests(TestCase):
    """Test suite for the Organization ViewSet."""

    def setUp(self):
        """Set up test cases, creating users and organizations."""
        self.client = Client()

        # Create users using UserFactory (password is handled automatically)
        self.user1 = UserFactory(username="jdoe", email="jdoe@example.com")
        self.user2 = UserFactory(username="asmith", email="asmith@example.com")
        self.staff_user = UserFactory(
            username="admin", email="admin@example.com", is_staff=True
        )

        # Create organizations using OrganizationFactory
        self.organization1 = OrganizationFactory(
            name="Example Organization 1", slug="example-org-1"
        )
        self.organization2 = OrganizationFactory(
            name="Example Organization 2", slug="example-org-2"
        )

        # Add users to organizations
        self.organization1.users.add(self.user1)
        self.organization2.users.add(self.user1, self.user2)

        # API URLs
        self.list_url = reverse("api2-organizations-list")
        self.detail_url = reverse(
            "api2-organizations-detail", args=[self.organization1.uuid]
        )

    def test_list_organizations_staff(self):
        """Test staff users can list all organizations."""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that both organizations are returned
        response_data = response.json()
        organization_names = [org["name"] for org in response_data]
        self.assertIn("Example Organization 1", organization_names)
        self.assertIn("Example Organization 2", organization_names)

    def test_list_organizations_non_staff(self):
        """Test non-staff users can only list organizations they belong to."""
        self.client.force_login(self.user2)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that user2 only sees the organizations they belong to
        response_data = response.json()
        organization_names = [org["name"] for org in response_data]
        self.assertIn("Example Organization 2", organization_names)
        self.assertNotIn("Example Organization 1", organization_names)

    def test_filter_organizations_by_name(self):
        """Test filtering organizations by name."""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.list_url, {"name": "Example Organization 1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the filtered organization is returned
        response_data = response.json()
        organization_names = [org["name"] for org in response_data]
        self.assertIn("Example Organization 1", organization_names)
        self.assertNotIn("Example Organization 2", organization_names)

    def test_filter_organizations_by_slug(self):
        """Test filtering organizations by slug."""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.list_url, {"slug": "example-org-1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the filtered organization is returned
        response_data = response.json()
        organization_slugs = [org["slug"] for org in response_data]
        self.assertIn("example-org-1", organization_slugs)
        self.assertNotIn("example-org-2", organization_slugs)

    def test_filter_organizations_by_uuid(self):
        """Test filtering organizations by UUID."""
        self.client.force_login(self.staff_user)
        response = self.client.get(
            self.list_url, {"uuid": str(self.organization1.uuid)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the filtered organization is returned
        response_data = response.json()
        organization_uuids = [org["uuid"] for org in response_data]
        self.assertIn(str(self.organization1.uuid), organization_uuids)
        self.assertNotIn(str(self.organization2.uuid), organization_uuids)

    def test_access_organization_detail_non_staff(self):
        """Test that non-staff users can access their own organization details."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("api2-organizations-detail", args=[self.organization1.uuid])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the correct organization data is returned
        response_data = response.json()
        self.assertEqual(response_data["name"], "Example Organization 1")
        self.assertEqual(response_data["slug"], "example-org-1")

    def test_access_organization_detail_non_member(self):
        """Test that non-staff users cannot access organizations they don't belong to."""
        self.client.force_login(self.user2)
        response = self.client.get(
            reverse("api2-organizations-detail", args=[self.organization1.uuid])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
