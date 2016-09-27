"""
Test the views of jurisdiction models
"""

from django.test import TestCase

from nose.tools import eq_, ok_

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

    def test_unique_for_jurisdiction(self):
        """Two exemptions may have the same name,
        as long as they belong to different jurisdictions."""
        another_jurisdiction = factories.StateJurisdictionFactory()
        ok_(self.exemption.jurisdiction is not another_jurisdiction)
        factories.ExemptionFactory(jurisdiction=another_jurisdiction)
        response = http_get_response(self.url, self.view, **self.kwargs)
        eq_(response.status_code, 200)

    def test_local_exemptions(self):
        """An exemption at the local level should return 200."""
        local = factories.LocalJurisdictionFactory()
        exemption = factories.ExemptionFactory(jurisdiction=local)
        url = exemption.get_absolute_url()
        kwargs = exemption.jurisdiction.get_slugs()
        kwargs.update({
            'slug': exemption.slug,
            'pk': exemption.pk
        })
        response = http_get_response(url, self.view, **kwargs)
        eq_(response.status_code, 200)

    def test_state_exemptions(self):
        """An exemption at the state level should return 200."""
        state = factories.StateJurisdictionFactory()
        exemption = factories.ExemptionFactory(jurisdiction=state)
        url = exemption.get_absolute_url()
        kwargs = exemption.jurisdiction.get_slugs()
        kwargs.update({
            'slug': exemption.slug,
            'pk': exemption.pk
        })
        response = http_get_response(url, self.view, **kwargs)
        eq_(response.status_code, 200)

    def test_federal_exemptions(self):
        """An exemption at the federal level should return 200."""
        fed = factories.FederalJurisdictionFactory()
        exemption = factories.ExemptionFactory(jurisdiction=fed)
        url = exemption.get_absolute_url()
        kwargs = exemption.jurisdiction.get_slugs()
        kwargs.update({
            'slug': exemption.slug,
            'pk': exemption.pk,
        })
        response = http_get_response(url, self.view, **kwargs)
        eq_(response.status_code, 200)
