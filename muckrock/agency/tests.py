"""
Tests for Agency application
"""

from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase, RequestFactory

from datetime import datetime, timedelta
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

    def test_agency_is_stale(self):
        """Should return the date of the last response by the agency"""
        duration = agency.models.STALE_DURATION + 1
        comm_date = datetime.today() - timedelta(duration)
        factories.FOIACommunicationFactory(
            date=comm_date,
            response=True,
            foia__status='ack',
            foia__agency=self.agency1
        )
        eq_(self.agency1.is_stale(), True,
            "The agency should report the days since its latest response.")

class TestAgencyManager(TestCase):
    """Tests for the Agency object manager"""
    def setUp(self):
        self.agency1 = factories.AgencyFactory()
        self.agency2 = factories.AgencyFactory(
                jurisdiction=self.agency1.jurisdiction)
        self.agency3 = factories.AgencyFactory(
                jurisdiction=self.agency1.jurisdiction,
                status='pending')

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
        self.request_factory = RequestFactory()
        self.agency = factories.AgencyFactory()
        self.request = self.request_factory.get(self.agency.get_absolute_url())
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
        self.agency.status = 'pending'
        self.agency.save()
        jurisdiction = self.agency.jurisdiction
        self.view(
            self.request,
            jurisdiction.slug,
            jurisdiction.pk,
            self.agency.slug,
            self.agency.pk
        )

    def test_list(self):
        """The list should only contain approved agencies"""
        approved_agency = factories.AgencyFactory()
        unapproved_agency = factories.AgencyFactory(status='pending')
        request = self.request_factory.get(reverse('agency-list'))
        view = agency.views.List.as_view()
        response = view(request)
        agency_list = response.context_data['object_list']
        ok_(approved_agency in agency_list, 'Approved agencies should be listed.')
        ok_(unapproved_agency not in agency_list, 'Unapproved agencies should not be listed.')


class TestAgencyForm(TestCase):
    """Tests the AgencyForm"""

    def setUp(self):
        self.agency = factories.AgencyFactory()
        self.form = agency.forms.AgencyForm({'name': self.agency.name}, instance=self.agency)

    def test_validate_empty_form(self):
        """The form should have a name, at least"""
        # pylint: disable=no-self-use
        ok_(not agency.forms.AgencyForm().is_valid(),
            'Empty AgencyForm should not validate.')

    def test_instance_form(self):
        """The form should validate given only instance data"""
        ok_(self.form.is_valid())


class TestStaleAgency(TestCase):
    """Tests the stale agency task"""
    def setUp(self):
        self.stale_agency = factories.StaleAgencyFactory()

    def test_stale_task(self):
        """A stale agency should be marked as stale"""
        from muckrock.agency.tasks import stale
        # The stale agency factory marks it as Stale by default, for convenience.
        # So, we lower to stale flag to make sure it's actually raised!
        self.stale_agency.stale = False
        self.stale_agency.save()
        ok_(not self.stale_agency.stale)
        stale()
        self.stale_agency.refresh_from_db()
        ok_(self.stale_agency.stale, 'The agency should be marked as stale')
