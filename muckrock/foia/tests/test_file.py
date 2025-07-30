"""
Files should be added to communications
"""

# Django
from django.http import Http404
from django.test import TestCase
from django.urls import reverse

# Third Party
import pytest

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.core.test_utils import http_get_response
from muckrock.foia.factories import FOIAFileFactory
from muckrock.foia.views import FOIAFileListView


class TestRequestFilesView(TestCase):
    """Files should render in a paginated list on a separate page."""

    def setUp(self):
        self.file = FOIAFileFactory()
        self.foia = self.file.comm.foia
        self.kwargs = {
            "idx": self.foia.pk,
            "slug": self.foia.slug,
            "jidx": self.foia.jurisdiction.pk,
            "jurisdiction": self.foia.jurisdiction.slug,
        }
        self.url = reverse("foia-files", kwargs=self.kwargs)
        self.view = FOIAFileListView.as_view()

    def test_get_ok(self):
        """The view should return 200 if the foia is viewable to the user."""
        assert self.foia.has_perm(
            self.foia.user, "view"
        ), "The user should be able to view the request"
        response = http_get_response(self.url, self.view, self.foia.user, **self.kwargs)
        assert response.status_code == 200, "The view should return 200."

    def test_get_404(self):
        """The view should return 404 is the foia is not visible to the user."""
        self.foia.embargo_status = "embargo"
        self.foia.save()
        user = UserFactory()
        assert not self.foia.has_perm(user, "view")
        with pytest.raises(Http404):
            http_get_response(self.url, self.view, user, **self.kwargs)
