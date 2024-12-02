""" Test jurisdiction views """

# Django
from django.test import TestCase
from django.urls import reverse

# Third Party
from rest_framework import status
from rest_framework.test import APIClient

# MuckRock
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

        # Create jurisdictions and store in a dictionary for easy access
        self.jurisdictions = {
            "springfield": LocalJurisdictionFactory.create(name="Springfield"),
            "spring": LocalJurisdictionFactory.create(name="Springville"),
            "MO": LocalJurisdictionFactory.create(name="Missouri", abbrev="MO"),
            "MI": LocalJurisdictionFactory.create(name="Michigan", abbrev="MI"),
            "federal": FederalJurisdictionFactory.create(name="Federal Test Agency", abbrev="FSA"),
            "state": StateJurisdictionFactory.create(name="State Test Agency", abbrev="STA"),
        }

    def test_list(self):
        """Test retrieving the list of jurisdictions."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_names = [jurisdiction["name"] for jurisdiction in response_data]

        # Check that all six jurisdictions returned
        assert len(jurisdiction_names) == 6

    def test_filter_by_name(self):
        """Test filtering jurisdictions by name."""
        response = self.client.get(self.url, {"name": "spring"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_names = [jurisdiction["name"] for jurisdiction in response_data]

        # Check that both jurisdictions are present in the response
        self.assertIn("Springfield", jurisdiction_names)
        self.assertIn("Springville", jurisdiction_names)
        assert len(jurisdiction_names) == 2

    def test_filter_by_abbrev(self):
        """Test filtering jurisdictions by abbreviation."""
        response = self.client.get(self.url, {"abbrev": "MO"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_abbrevs = [
            jurisdiction["abbrev"] for jurisdiction in response_data
        ]

        # Check that the expected jurisdiction is present
        self.assertIn("MO", jurisdiction_abbrevs)
        self.assertNotIn(
            "MI", jurisdiction_abbrevs
        )  # Ensure the other abbreviation is not present
        assert len(jurisdiction_abbrevs) == 1

    def test_filter_by_level(self):
        """Test filtering jurisdictions by level."""
        response = self.client.get(self.url, {"level": "s"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Access the response data
        response_data = response.json()
        jurisdiction_levels = [jurisdiction["level"] for jurisdiction in response_data]

        # Check that the expected jurisdiction is present
        self.assertIn("s", jurisdiction_levels)
        self.assertNotIn(
            "f", jurisdiction_levels
        )  # Ensure that unexpected levels are not present
        self.assertNotIn(
            "l", jurisdiction_levels
        )
        assert len(jurisdiction_levels) == 1
