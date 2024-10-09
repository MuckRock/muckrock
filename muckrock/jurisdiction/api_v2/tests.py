# Django
from django.test import TestCase
from django.urls import reverse

# Third Party
from nose.tools import eq_
from rest_framework.test import APIClient

# MuckRock
from muckrock.jurisdiction.factories import JurisdictionFactory

class TestJurisdictionViewSet(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.jurisdiction1 = JurisdictionFactory.create(name="Springfield")
        self.jurisdiction2 = JurisdictionFactory.create(name="Spring")

    def test_detail(self):
        response = self.client.get(
            reverse("api2-jurisdictions-detail", kwargs={"pk": self.jurisdiction1.pk}),
        )
        eq_(response.status_code, 200)
        eq_(response.data["id"], self.jurisdiction1.pk)  # Check if the returned ID matches

    def test_list(self):
        response = self.client.get(reverse("api2-jurisdictions-list"))
        eq_(response.status_code, 200)
        eq_(len(response.data), 2)  # Expecting two jurisdictions in the response

    def test_filter_by_name(self):
        response = self.client.get(reverse("api2-jurisdictions-list"), {"name": "spring"})
        eq_(response.status_code, 200)
        eq_(len(response.data), 2)  # Expecting both jurisdictions to match

    def test_filter_by_abbrev(self):
        jurisdiction3 = JurisdictionFactory.create(abbrev="TJ")
        jurisdiction4 = JurisdictionFactory.create(abbrev="TJ2")
        
        response = self.client.get(reverse("api2-jurisdictions-list"), {"abbrev": "TJ"})
        eq_(response.status_code, 200)
        eq_(len(response.data), 1)  # Expecting one jurisdiction to match

    def test_filter_by_level(self):
        jurisdiction5 = JurisdictionFactory.create(level="Federal")
        jurisdiction6 = JurisdictionFactory.create(level="State")

        response = self.client.get(reverse("api2-jurisdictions-list"), {"level": "State"})
        eq_(response.status_code, 200)
        eq_(len(response.data), 1)  # Expecting one jurisdiction to match
