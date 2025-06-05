""" Tests for the Agency API """

# Django
from django.test import Client
from django.urls import reverse

# Third Party
from rest_framework import status
from rest_framework.test import APITestCase

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.jurisdiction.factories import LocalJurisdictionFactory


class AgencyViewSetTests(APITestCase):
    """Test suite for the Agency ViewSet."""

    def setUp(self):
        """Set up test cases, creating jurisdictions, agencies, and users."""
        # Create test jurisdictions
        self.jurisdictions = [
            LocalJurisdictionFactory.create(name="1st Jurisdiction"),
            LocalJurisdictionFactory.create(name="2nd Jurisdiction"),
        ]

        # Create agencies
        self.agencies = [
            AgencyFactory.create(
                name="First Approved Agency",
                jurisdiction=self.jurisdictions[0],
                status="approved",
            ),
            AgencyFactory.create(
                name="Unapproved Agency",
                jurisdiction=self.jurisdictions[0],
                status="unapproved",
            ),
            AgencyFactory.create(
                name="Second Approved Agency",
                jurisdiction=self.jurisdictions[1],
                status="approved",
            ),
        ]

        # URL for the agency list
        self.url = reverse("agency-list")

        # Create users
        self.user1 = UserFactory(username="adam", is_staff=True)
        self.user2 = UserFactory(username="bob", is_staff=False)

        self.client = Client()

    def test_retrieve_agencies(self):
        """Test retrieving the list of agencies."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fuzzy_search_agency_name(self):
        """Test fuzzy searching by agency name."""
        response = self.client.get(self.url, {"search": "second"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertIn("Second Approved Agency", agency_names)
        self.assertNotIn("First Approved Agency", agency_names)
        self.assertNotIn("Unapproved Agency", agency_names)

    def test_fuzzy_search_jurisdiction_name(self):
        """Test fuzzy searching by jurisdiction name."""
        response = self.client.get(self.url, {"search": "1st"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertNotIn("Second Approved Agency", agency_names)

    def test_non_approved_agencies_hidden(self):
        """Test that non-approved agencies are hidden for non-staff users."""
        self.client.force_login(self.user2)  # Ensure we are logged in as non-staff user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertIn("First Approved Agency", agency_names)
        self.assertNotIn("Unapproved Agency", agency_names)

    def test_staff_user_can_see_all_agencies(self):
        """Test that staff users can see all agencies."""
        self.client.force_login(self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertIn("First Approved Agency", agency_names)
        self.assertIn("Second Approved Agency", agency_names)
        self.assertIn("Unapproved Agency", agency_names)

    def test_ordering(self):
        """Test that agencies are returned in the correct order."""
        response = self.client.get(self.url, {"ordering": "name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        # Assuming the expected order based on names
        self.assertEqual(
            agency_names,
            ["First Approved Agency", "Second Approved Agency", "Unapproved Agency"],
        )
