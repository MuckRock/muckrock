"""
Tests for Jurisdiction application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase
import nose.tools

from jurisdiction.models import Jurisdiction

# allow methods that could be functions and too many public methods in tests
# pylint: disable=R0201
# pylint: disable=R0904

class TestJurisdictionUnit(TestCase):
    """Unit tests for Jurisdictions"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_agencies.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        self.state = Jurisdiction.objects.get(pk=1)
        self.local = Jurisdiction.objects.get(pk=3)

    def test_jurisdiction_unicode(self):
        """Test Jurisdiction model's __unicode__ method"""
        nose.tools.eq_(unicode(self.state), u'Massachusetts')
        nose.tools.eq_(unicode(self.local), u'Boston, MA')

    def test_jurisdiction_url(self):
        """Test Jurisdiction model's get_absolute_url method"""
        nose.tools.eq_(self.state.get_absolute_url(),
            reverse('jurisdiction-detail',
                    kwargs={'idx': self.state.pk, 'slug': 'massachusetts'}))

    def test_jurisdiction_legal(self):
        """Test Jurisdiction model's legal method"""
        nose.tools.eq_(self.state.legal(), 'MA')
        nose.tools.eq_(self.local.legal(), 'MA')

    def test_jurisdiction_get_days(self):
        """Test Jurisdiction model's get days method"""
        nose.tools.eq_(self.state.get_days(), 10)
        nose.tools.eq_(self.local.get_days(), 10)
