"""
Files should be added to communications
"""

# Django
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase

# Third Party
from nose.tools import eq_, ok_, raises

# MuckRock
from muckrock.factories import FOIAFileFactory, UserFactory
from muckrock.foia.views import FOIAFileListView
from muckrock.test_utils import http_get_response


class TestRequestFilesView(TestCase):
    """Files should render in a paginated list on a separate page."""

    def setUp(self):
        self.file = FOIAFileFactory()
        self.foia = self.file.comm.foia
        self.kwargs = {
            'idx': self.foia.pk,
            'slug': self.foia.slug,
            'jidx': self.foia.jurisdiction.pk,
            'jurisdiction': self.foia.jurisdiction.slug
        }
        self.url = reverse('foia-files', kwargs=self.kwargs)
        self.view = FOIAFileListView.as_view()

    def test_get_ok(self):
        """The view should return 200 if the foia is viewable to the user."""
        ok_(
            self.foia.has_perm(self.foia.user, 'view'),
            'The user should be able to view the request'
        )
        response = http_get_response(
            self.url, self.view, self.foia.user, **self.kwargs
        )
        eq_(response.status_code, 200, 'The view should return 200.')

    @raises(Http404)
    def test_get_404(self):
        """The view should return 404 is the foia is not visible to the user."""
        self.foia.embargo = True
        self.foia.save()
        user = UserFactory()
        ok_(not self.foia.has_perm(user, 'view'))
        http_get_response(self.url, self.view, user, **self.kwargs)
