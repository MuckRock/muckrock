from django.test import TestCase

from nose.tools import eq_

from muckrock.factories import UserFactory, FOIARequestFactory
from muckrock.foia.views import Detail
from muckrock.test_utils import http_post_response

class TestFOIANotes(TestCase):
    """Allow editors to attach notes to a request."""
    def setUp(self):
        self.foia = FOIARequestFactory()
        self.editor = UserFactory()
        self.viewer = UserFactory()
        self.foia.add_editor(self.editor)
        self.foia.add_viewer(self.viewer)
        self.data = {'action': 'add_note', 'note': u'Lorem ipsum dolor su ament.'}
        self.url = self.foia.get_absolute_url()
        self.view = Detail.as_view()
        self.kwargs = {
            'jurisdiction': self.foia.jurisdiction.slug,
            'jidx': self.foia.jurisdiction.id,
            'slug': self.foia.slug,
            'idx': self.foia.id
        }

    def test_add_note(self):
        """User with edit permission should be able to create a note."""
        response = http_post_response(self.url, self.view, self.data, self.editor, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        eq_(self.foia.notes.count() > 0, True)

    def test_add_note_without_permission(self):
        """Normies and viewers cannot add notes."""
        response = http_post_response(self.url, self.view, self.data, self.viewer, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        eq_(self.foia.notes.count(), 0)
