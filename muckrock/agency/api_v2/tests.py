"""Tests for the Agency API"""

# Django
from django.urls import reverse

# Third Party
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

# MuckRock
from muckrock.agency.models import AgencyType
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.core.test_utils import assert_queries_do_not_scale
from muckrock.jurisdiction.factories import (
    FederalJurisdictionFactory,
    LocalJurisdictionFactory,
    StateJurisdictionFactory,
)


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
                status="rejected",
            ),
            AgencyFactory.create(
                name="Second Approved Agency",
                jurisdiction=self.jurisdictions[1],
                status="approved",
            ),
        ]

        # URL for the agency list
        self.url = reverse("api2-agencies-list")

        # Create users
        self.user1 = UserFactory(username="adam", is_staff=True)
        self.user2 = UserFactory(username="bob", is_staff=False)

        self.client = APIClient()

    def test_list_queries_do_not_scale(self):
        """Listing agencies must not add queries as the number of agencies grows."""
        self.client.force_authenticate(user=self.user1)
        assert_queries_do_not_scale(
            self.client,
            self.url,
            lambda: AgencyFactory(status="approved"),
        )

    def test_retrieve_agencies(self):
        """Test retrieving the list of agencies."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fuzzy_search_agency_name(self):
        """Test fuzzy searching by agency name."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url, {"search": "second"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertIn("Second Approved Agency", agency_names)
        self.assertNotIn("First Approved Agency", agency_names)
        self.assertNotIn("Unapproved Agency", agency_names)

    def test_fuzzy_search_jurisdiction_name(self):
        """Test fuzzy searching by jurisdiction name."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url, {"search": "1st"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertNotIn("Second Approved Agency", agency_names)

    def test_rejected_agencies_hidden(self):
        """Test that non-approved agencies are hidden for non-staff users."""
        self.client.force_authenticate(
            user=self.user2
        )  # Ensure we are logged in as non-staff user
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertIn("First Approved Agency", agency_names)
        self.assertNotIn("Unapproved Agency", agency_names)

    def test_staff_user_can_see_all_agencies(self):
        """Test that staff users can see all agencies."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        agency_names = [agency["name"] for agency in response_data["results"]]

        self.assertIn("First Approved Agency", agency_names)
        self.assertIn("Second Approved Agency", agency_names)
        self.assertIn("Unapproved Agency", agency_names)

    def test_unauthenticated_user_cannot_list_agencies(self):
        """Test that unauthenticated users cannot access the agency list."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_retrieve_agency(self):
        """Test that unauthenticated users cannot retrieve a single agency."""
        url = reverse("api2-agencies-detail", args=[self.agencies[0].pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _names(self, response):
        """Sorted agency names from a list response"""
        return sorted(agency["name"] for agency in response.json()["results"])

    def _create_typed_agencies(self):
        """Agencies with known types"""
        police, _ = AgencyType.objects.get_or_create(name="Police")
        executive, _ = AgencyType.objects.get_or_create(name="Executive")
        AgencyFactory.create(
            name="Burlington Police Department", status="approved"
        ).types.add(police)
        AgencyFactory.create(
            name="Concord Police Department", status="approved"
        ).types.add(police)
        AgencyFactory.create(
            name="Office of the Governor", status="approved"
        ).types.add(executive)

    def test_filter_by_type(self):
        """type matches the agency type name, case-insensitive"""
        self.client.force_authenticate(user=self.user2)
        self._create_typed_agencies()
        response = self.client.get(self.url, {"type": "POLICE"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert self._names(response) == [
            "Burlington Police Department",
            "Concord Police Department",
        ]

    def test_filter_by_type_is_exact(self):
        """A partial type name matches nothing"""
        self.client.force_authenticate(user=self.user2)
        self._create_typed_agencies()
        response = self.client.get(self.url, {"type": "pol"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert self._names(response) == []

    def _create_state_agencies(self):
        """Agencies at the state, local, other-state and federal levels"""
        vermont = StateJurisdictionFactory.create(name="Vermont", abbrev="VT")
        burlington = LocalJurisdictionFactory.create(name="Burlington", parent=vermont)
        new_hampshire = StateJurisdictionFactory.create(
            name="New Hampshire", abbrev="NH"
        )
        federal = FederalJurisdictionFactory.create(
            name="United States of America Test", abbrev="UST"
        )
        AgencyFactory.create(
            name="Vermont State Police", jurisdiction=vermont, status="approved"
        )
        AgencyFactory.create(
            name="Burlington Police Department",
            jurisdiction=burlington,
            status="approved",
        )
        AgencyFactory.create(
            name="New Hampshire State Police",
            jurisdiction=new_hampshire,
            status="approved",
        )
        AgencyFactory.create(
            name="Federal Bureau of Investigation",
            jurisdiction=federal,
            status="approved",
        )
        return vermont, burlington

    def test_filter_by_state(self):
        """state matches agencies in the state and its local jurisdictions"""
        self.client.force_authenticate(user=self.user2)
        vermont, _ = self._create_state_agencies()
        response = self.client.get(self.url, {"state": vermont.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert self._names(response) == [
            "Burlington Police Department",
            "Vermont State Police",
        ]

    def test_filter_by_state_ignores_local_ids(self):
        """Passing a local jurisdiction's ID as state matches nothing"""
        self.client.force_authenticate(user=self.user2)
        _, burlington = self._create_state_agencies()
        response = self.client.get(self.url, {"state": burlington.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert self._names(response) == []
