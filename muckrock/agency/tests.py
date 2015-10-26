"""
Tests for Agency application
"""

from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase, RequestFactory

import nose.tools

from muckrock import agency
from muckrock import factories
from muckrock.utils import mock_middleware

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

class TestAgencyUnit(TestCase):
    """Unit tests for Agencies"""

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        self.agency1 = factories.AgencyFactory(
            fax='1-987-654-3210',
            email='test@agency1.gov',
            other_emails='other_a@agency1.gov, other_b@agency1.gov'
        )
        self.agency2 = factories.AgencyFactory(
            fax='987.654.3210',
            email=''
        )
        self.agency3 = factories.AgencyFactory()

    def test_agency_url(self):
        """Test Agency model's get_absolute_url method"""
        eq_(self.agency1.get_absolute_url(), reverse('agency-detail', kwargs={
                'idx': self.agency1.pk,
                'slug': self.agency1.slug,
                'jurisdiction': self.agency1.jurisdiction.slug,
                'jidx': self.agency1.jurisdiction.pk
            })
        )

    def test_agency_normalize_fax(self):
        """Test the normalize fax method"""
        normalized = '19876543210'
        eq_(self.agency1.normalize_fax(), normalized)
        eq_(self.agency2.normalize_fax(), normalized)
        eq_(self.agency3.normalize_fax(), None)

    def test_agency_get_email(self):
        """Test the get email method"""
        eq_(self.agency1.get_email(), 'test@agency1.gov')
        eq_(self.agency2.get_email(), '19876543210@fax2.faxaway.com')
        eq_(self.agency3.get_email(), '')

    def test_agency_get_other_emails(self):
        """Test get other emails method"""
        eq_(self.agency1.get_other_emails(), ['other_a@agency1.gov', 'other_b@agency1.gov'])


class TestAgencyManager(TestCase):
    """Tests for the Agency object manager"""
    def setUp(self):
        self.agency1 = factories.AgencyFactory()
        self.agency2 = factories.AgencyFactory(jurisdiction=self.agency1.jurisdiction)
        self.agency3 = factories.AgencyFactory(jurisdiction=self.agency1.jurisdiction,
                                               approved=False)

    def test_get_approved(self):
        """Manager should return all approved agencies"""
        agencies = agency.models.Agency.objects.get_approved()
        ok_(self.agency1 in agencies)
        ok_(self.agency2 in agencies)
        ok_(self.agency3 not in agencies)

    def test_get_siblings(self):
        """Manager should return all siblings to a given agency"""
        agencies = agency.models.Agency.objects.get_siblings(self.agency1)
        ok_(self.agency1 not in agencies, 'The given agency shouldn\'t be its own sibling.')
        ok_(self.agency2 in agencies)
        ok_(self.agency3 not in agencies, 'Unapproved agencies shouldn\'t be siblings.')


class TestAgencyViews(TestCase):
    """Tests for Agency views"""
    def setUp(self):
        request_factory = RequestFactory()
        self.agency = factories.AgencyFactory()
        self.request = request_factory.get(self.agency.get_absolute_url())
        self.request.user = factories.UserFactory()
        self.request = mock_middleware(self.request)
        self.view = agency.views.detail

    def test_approved_ok(self):
        """An approved agency should return an 200 response."""
        jurisdiction = self.agency.jurisdiction
        response = self.view(
            self.request,
            jurisdiction.slug,
            jurisdiction.pk,
            self.agency.slug,
            self.agency.pk
        )
        eq_(response.status_code, 200)

    @nose.tools.raises(Http404)
    def test_unapproved_not_found(self):
        """An unapproved agency should return a 404 response."""
        self.agency.approved = False
        self.agency.save()
        jurisdiction = self.agency.jurisdiction
        response = self.view(
            self.request,
            jurisdiction.slug,
            jurisdiction.pk,
            self.agency.slug,
            self.agency.pk
        )


class TestAgencyForm(TestCase):
    """Tests the AgencyForm"""

    def setUp(self):
        self.agency = factories.AgencyFactory()
        self.form = agency.forms.AgencyForm({'name': self.agency.name}, instance=self.agency)

    def test_validate_empty_form(self):
        """The form should have a name, at least"""
        ok_(not agency.forms.AgencyForm().is_valid(),
            'Empty AgencyForm should not validate.')

    def test_instance_form(self):
        """The form should validate given only instance data"""
        ok_(self.form.is_valid())
