"""
Tests for Agency application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase
import nose.tools

from agency.models import Agency

# allow methods that could be functions and too many public methods in tests
# pylint: disable=R0201
# pylint: disable=R0904

class TestAgencyUnit(TestCase):
    """Unit tests for Agencies"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_agencies.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        self.agency = Agency.objects.get(pk=1)

    def test_agency_unicode(self):
        """Test Agency model's __unicode__ method"""
        nose.tools.eq_(unicode(self.agency), u'Test Agency')

    def test_agency_url(self):
        """Test Agency model's get_absolute_url method"""
        nose.tools.eq_(self.agency.get_absolute_url(),
            reverse('agency-detail', kwargs={'idx': self.agency.pk, 'slug': 'test-agency',
                                             'jurisdiction': 'cambridge-ma'}))

    def test_agency_normalize_fax(self):
        """Test the normalize fax method"""
        nose.tools.eq_(Agency.objects.get(pk=1).normalize_fax(), '19876543210')
        nose.tools.eq_(Agency.objects.get(pk=2).normalize_fax(), '19876543210')
        nose.tools.eq_(Agency.objects.get(pk=3).normalize_fax(), None)

    def test_agency_get_email(self):
        """Test the get email method"""
        nose.tools.eq_(Agency.objects.get(pk=1).get_email(), 'test@agency1.gov')
        nose.tools.eq_(Agency.objects.get(pk=2).get_email(), '19876543210@fax2.faxaway.com')
        nose.tools.eq_(Agency.objects.get(pk=3).get_email(), '')

    def test_agency_get_other_emails(self):
        """Test get other emails method"""
        nose.tools.eq_(self.agency.get_other_emails(),
                       ['other_a@agency1.gov', 'other_b@agency1.gov'])
