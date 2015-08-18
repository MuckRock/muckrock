"""
Tests for Agency application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase
import nose.tools

from muckrock.agency.models import Agency
from muckrock.agency.forms import AgencyForm
from muckrock.tests import get_allowed, get_404

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

# allow methods that could be functions and too many public methods in tests
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

class TestAgencyUnit(TestCase):
    """Unit tests for Agencies"""
    fixtures = ['test_users.json', 'holidays.json', 'jurisdictions.json', 'agency_types.json',
                'test_agencies.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        self.agency = Agency.objects.get(pk=1)

    def test_agency_unicode(self):
        """Test Agency model's __unicode__ method"""
        eq_(unicode(self.agency), u'Test Agency')

    def test_agency_url(self):
        """Test Agency model's get_absolute_url method"""
        eq_(
            self.agency.get_absolute_url(),
            reverse('agency-detail', kwargs={
                'idx': self.agency.pk,
                'slug': 'test-agency',
                'jurisdiction': 'cambridge-ma',
                'jidx': self.agency.jurisdiction.pk
            })
        )

    def test_agency_normalize_fax(self):
        """Test the normalize fax method"""
        eq_(Agency.objects.get(pk=1).normalize_fax(), '19876543210')
        eq_(Agency.objects.get(pk=2).normalize_fax(), '19876543210')
        eq_(Agency.objects.get(pk=3).normalize_fax(), None)

    def test_agency_get_email(self):
        """Test the get email method"""
        eq_(Agency.objects.get(pk=1).get_email(), 'test@agency1.gov')
        eq_(Agency.objects.get(pk=2).get_email(), '19876543210@fax2.faxaway.com')
        eq_(Agency.objects.get(pk=3).get_email(), '')

    def test_agency_get_other_emails(self):
        """Test get other emails method"""
        eq_(self.agency.get_other_emails(),
                       ['other_a@agency1.gov', 'other_b@agency1.gov'])

class TestAgencyViews(TestCase):
    """Tests for Agency views"""
    fixtures = ['test_users.json', 'holidays.json', 'jurisdictions.json', 'agency_types.json',
                'test_agencies.json', 'test_foiarequests.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        self.agency = Agency.objects.get(pk=1)

    def test_detail(self):
        """Test the detail view"""

        get_allowed(self.client,
                    reverse('agency-detail',
                            kwargs={'jurisdiction': self.agency.jurisdiction.slug,
                                    'jidx': self.agency.jurisdiction.pk,
                                    'slug': self.agency.slug, 'idx': self.agency.pk}),
                    ['profile/agency.html', 'base_profile.html'],
                    context={'agency': self.agency})

        get_404(self.client,
                reverse('agency-detail',
                        kwargs={'jurisdiction': 'fake-jurisdiction',
                                'jidx': self.agency.jurisdiction.pk,
                                'slug': self.agency.slug, 'idx': self.agency.pk}))
        get_404(self.client,
                reverse('agency-detail',
                        kwargs={'jurisdiction': self.agency.jurisdiction.slug,
                                'jidx': self.agency.jurisdiction.pk,
                                'slug': 'fake-slug', 'idx': self.agency.pk}))

        agency = Agency.objects.get(pk=3)
        get_404(self.client,
                reverse('agency-detail',
                        kwargs={'jurisdiction': agency.jurisdiction.slug,
                                'jidx': self.agency.jurisdiction.pk,
                                'slug': agency.slug, 'idx': agency.pk}))

class TestAgencyForm(TestCase):
    """Tests the AgencyForm"""
    fixtures = ['test_users.json', 'holidays.json', 'jurisdictions.json', 'agency_types.json',
                'test_agencies.json', 'test_foiarequests.json']

    def setUp(self):
        self.agency = Agency.objects.get(pk=1)
        self.form = AgencyForm({'name': 'Test Agency'}, instance=self.agency)

    def test_validate_empty_form(self):
        """The form should have a name, at least"""
        ok_(not AgencyForm().is_valid(),
            'Empty AgencyForm should not validate.')

    def test_instance_form(self):
        """The form should validate given only instance data"""
        ok_(self.form.is_valid())
