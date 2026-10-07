"""Test jurisdiction views"""

# Django
from django.test import TestCase
from django.urls import reverse

# Third Party
from rest_framework import status
from rest_framework.test import APIClient

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.core.test_utils import assert_queries_do_not_scale
from muckrock.jurisdiction.factories import (
    FederalJurisdictionFactory,
    LocalJurisdictionFactory,
    StateJurisdictionFactory,
)


class JurisdictionViewSetTests(TestCase):
    """Test suite for the Jurisdiction ViewSet."""

    def setUp(self):
        """Set up test cases, creating jurisdictions."""
        self.client = APIClient()
        self.url = reverse("api2-jurisdictions-list")
        self.user = UserFactory.create()

        # Create jurisdictions and store in a dictionary for easy access
        self.jurisdictions = {
            "springfield": LocalJurisdictionFactory.create(name="Springfield"),
            "spring": LocalJurisdictionFactory.create(name="Springville"),
            "MO": LocalJurisdictionFactory.create(name="Missouri", abbrev="MO"),
            "MI": LocalJurisdictionFactory.create(name="Michigan", abbrev="MI"),
            "federal": FederalJurisdictionFactory.create(
                name="Federal Test Agency", abbrev="FSA"
            ),
            "state": StateJurisdictionFactory.create(
                name="State Test Agency", abbrev="STA"
            ),
        }

    def test_list(self):
        """Test retrieving the list of jurisdictions."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_names = [
            jurisdiction["name"] for jurisdiction in response_data["results"]
        ]

        for name in [
            "Springfield",
            "Springville",
            "Missouri",
            "Michigan",
            "Federal Test Agency",
            "State Test Agency",
        ]:
            assert name in jurisdiction_names

    def test_filter_by_name(self):
        """Test filtering jurisdictions by name."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {"name": "spring"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_names = [
            jurisdiction["name"] for jurisdiction in response_data["results"]
        ]

        # Check that both jurisdictions are present in the response
        self.assertIn("Springfield", jurisdiction_names)
        self.assertIn("Springville", jurisdiction_names)
        assert len(jurisdiction_names) == 2

    def test_filter_by_abbrev(self):
        """Test filtering jurisdictions by abbreviation."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {"abbrev": "MO"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_abbrevs = [
            jurisdiction["abbrev"] for jurisdiction in response_data["results"]
        ]

        # Check that the expected jurisdiction is present
        self.assertIn("MO", jurisdiction_abbrevs)
        self.assertNotIn(
            "MI", jurisdiction_abbrevs
        )  # Ensure the other abbreviation is not present
        assert len(jurisdiction_abbrevs) == 1

    def test_filter_by_level(self):
        """Test filtering jurisdictions by level."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {"level": "s"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_levels = [
            jurisdiction["level"] for jurisdiction in response_data["results"]
        ]

        # Check that the expected jurisdiction is present
        self.assertIn("s", jurisdiction_levels)
        self.assertNotIn(
            "f", jurisdiction_levels
        )  # Ensure that unexpected levels are not present
        self.assertNotIn("l", jurisdiction_levels)

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_cannot_retrieve(self):
        url = reverse(
            "api2-jurisdictions-detail", args=[self.jurisdictions["springfield"].pk]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_queries_do_not_scale(self):
        """Listing jurisdictions must not add queries as jurisdictions grow"""
        self.client.force_authenticate(user=self.user)
        state = StateJurisdictionFactory.create(name="Scaling State", abbrev="SS")
        counter = iter(range(1, 100))

        def create_one():
            # Because jurisdictions have a uniqueness constraint on name
            # We differ each one made by the factory by the counter
            LocalJurisdictionFactory.create(
                name=f"Scaling Local {next(counter)}", parent=state
            )

        assert_queries_do_not_scale(self.client, self.url, create_one)

    def _create_family(self):
        """Two states with known local children"""
        vermont = StateJurisdictionFactory.create(name="Vermont", abbrev="VT")
        new_hampshire = StateJurisdictionFactory.create(
            name="New Hampshire", abbrev="NH"
        )
        LocalJurisdictionFactory.create(name="Burlington", parent=vermont)
        LocalJurisdictionFactory.create(name="Montpelier", parent=vermont)
        LocalJurisdictionFactory.create(name="Concord", parent=new_hampshire)

    def _names(self, response):
        """Sorted jurisdiction names from a list response"""
        return sorted(j["name"] for j in response.json()["results"])

    def test_filter_by_parent_name(self):
        """parent_name matches part of the parent's name, case-insensitive"""
        self.client.force_authenticate(user=self.user)
        self._create_family()
        response = self.client.get(self.url, {"parent_name": "VERM"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert self._names(response) == ["Burlington", "Montpelier"]

    def test_filter_by_parent_abbrev(self):
        """parent_abbrev matches the parent's full abbreviation, case-insensitive"""
        self.client.force_authenticate(user=self.user)
        self._create_family()
        response = self.client.get(self.url, {"parent_abbrev": "vt"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert self._names(response) == ["Burlington", "Montpelier"]

    def test_filter_by_parent_abbrev_is_exact(self):
        """A partial abbreviation matches nothing"""
        self.client.force_authenticate(user=self.user)
        self._create_family()
        response = self.client.get(self.url, {"parent_abbrev": "V"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assert self._names(response) == []
