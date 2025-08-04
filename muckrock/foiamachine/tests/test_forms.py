"""
Tests for FOIA Machine forms.
"""

# Django
from django.test import TestCase

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foiamachine import factories, forms
from muckrock.jurisdiction.factories import StateJurisdictionFactory


class TestFoiaMachineRequestForm(TestCase):
    """The FoiaMachineRequestForm provides for the creation of new requests."""

    def setUp(self):
        self.user = UserFactory()
        self.title = "Test Request"
        self.request_language = "Lorem ipsum"
        self.agency = AgencyFactory()
        self.jurisdiction = self.agency.jurisdiction
        self.foi = factories.FoiaMachineRequestFactory(
            user=self.user,
            title=self.title,
            request_language=self.request_language,
            jurisdiction=self.jurisdiction,
        )

    def test_basic(self):
        """A form should validate when given a title, a status, a request, and
        a jurisdiction."""
        form = forms.FoiaMachineRequestForm(
            {
                "title": self.title,
                "status": "started",
                "request_language": self.request_language,
                "jurisdiction": self.jurisdiction.id,
            }
        )
        assert form.is_valid()

    def test_agency(self):
        """The form should also accept an agency input."""
        form = forms.FoiaMachineRequestForm(
            {
                "title": self.title,
                "status": "started",
                "request_language": self.request_language,
                "jurisdiction": self.jurisdiction.id,
                "agency": self.agency.id,
            }
        )
        assert form.is_valid()

    def test_agency_mismatch(self):
        """The form should not validate if the agency is from a different
        jurisdiction."""
        jurisdiction = StateJurisdictionFactory()
        form = forms.FoiaMachineRequestForm(
            {
                "title": self.title,
                "status": "started",
                "request_language": self.request_language,
                "jurisdiction": jurisdiction.id,
                "agency": self.agency.id,
            }
        )
        assert not form.is_valid()
