"""
Users should be able to attach notes to requests
"""

# Django
from django.test import TestCase

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.core.test_utils import http_post_response
from muckrock.foia.factories import FOIARequestFactory
from muckrock.foia.views import Detail


class TestFOIANotes(TestCase):
    """Allow editors to attach notes to a request."""

    def setUp(self):
        self.foia = FOIARequestFactory()
        self.editor = UserFactory()
        self.viewer = UserFactory()
        self.foia.add_editor(self.editor)
        self.foia.add_viewer(self.viewer)
        self.data = {"action": "add_note", "note": "Lorem ipsum dolor su ament."}
        self.url = self.foia.get_absolute_url()
        self.view = Detail.as_view()
        self.kwargs = {
            "jurisdiction": self.foia.jurisdiction.slug,
            "jidx": self.foia.jurisdiction.id,
            "slug": self.foia.slug,
            "idx": self.foia.id,
        }
        UserFactory(username="MuckrockStaff")

    def test_add_note(self):
        """User with edit permission should be able to create a note."""
        response = http_post_response(
            self.url, self.view, self.data, self.editor, **self.kwargs
        )
        self.foia.refresh_from_db()
        assert response.status_code == 302
        assert self.foia.notes.count() > 0

    def test_add_sans_permission(self):
        """Normies and viewers cannot add notes."""
        response = http_post_response(
            self.url, self.view, self.data, self.viewer, **self.kwargs
        )
        self.foia.refresh_from_db()
        assert response.status_code == 302
        assert self.foia.notes.count() == 0
