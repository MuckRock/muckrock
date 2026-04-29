"""Tests for gethelp view integration with FOIA detail"""

# Django
from django.test import TestCase

# Standard Library
import json

# Third Party
import pytest

# MuckRock
from muckrock.core.factories import AgencyFactory, AppealAgencyFactory, UserFactory
from muckrock.core.test_utils import http_get_response
from muckrock.foia.factories import FOIARequestFactory
from muckrock.foia.views import Detail
from muckrock.gethelp.models import Problem


@pytest.mark.django_db
class TestGetHelpContext(TestCase):
    """Test that help problems are included in the FOIA detail context"""

    def setUp(self):
        agency = AgencyFactory(appeal_agency=AppealAgencyFactory())
        self.foia = FOIARequestFactory(agency=agency)
        self.view = Detail.as_view()
        self.url = self.foia.get_absolute_url()
        self.kwargs = {
            "jurisdiction": self.foia.jurisdiction.slug,
            "jidx": self.foia.jurisdiction.id,
            "slug": self.foia.slug,
            "idx": self.foia.id,
        }
        UserFactory(username="MuckrockStaff")

    def test_help_problems_in_context(self):
        """The help_problems_json key should be in the detail context"""
        response = http_get_response(self.url, self.view, self.foia.user, **self.kwargs)
        assert "help_problems_json" in response.context_data

    def test_help_problems_structure(self):
        """The context should contain the correct problem structure"""
        Problem.objects.create(
            category="managing",
            title="Test problem",
            resolution="**bold**",
        )
        response = http_get_response(self.url, self.view, self.foia.user, **self.kwargs)
        problems = response.context_data["help_problems_json"]
        assert isinstance(problems, dict)
        assert "managing" in problems
        assert len(problems["managing"]["problems"]) == 1
        assert problems["managing"]["problems"][0]["title"] == "Test problem"

    def test_help_problems_json_serializable(self):
        """The problems data can be serialized to JSON for the template"""
        Problem.objects.create(category="managing", title="Test")
        response = http_get_response(self.url, self.view, self.foia.user, **self.kwargs)
        problems = response.context_data["help_problems_json"]
        json_str = json.dumps(problems)
        assert json_str
