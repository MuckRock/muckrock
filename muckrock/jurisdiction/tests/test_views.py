"""
Test the views of jurisdiction models
"""

from django.test import TestCase

from nose.tools import eq_

from muckrock.jurisdiction import factories, views
from muckrock.test_utils import http_get_response

class TestExemptionDetailView(TestCase):
    """The exemption detail view provides information about the exemption at a standalone url."""
    def setUp(self):
        self.exemption = factories.ExemptionFactory()
        self.url = self.exemption.get_absolute_url()
        self.view = views.ExemptionDetailView.as_view()
        self.kwargs = self.exemption.jurisdiction.get_slugs()
        self.kwargs.update({
            'slug': self.exemption.slug,
            'pk': self.exemption.pk,
        })

    def test_ok(self):
        """The view should return a 200 OK status."""
        response = http_get_response(self.url, self.view, **self.kwargs)
        eq_(response.status_code, 200)
