"""
Tests for Jurisdiction application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase
import nose.tools

from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import Jurisdiction

# allow methods that could be functions and too many public methods in tests
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=bad-continuation

class TestJurisdictionUnit(TestCase):
    """Unit tests for Jurisdictions"""
    fixtures = ['test_users.json', 'holidays.json', 'jurisdictions.json', 'agency_types.json',
                'test_agencies.json', 'test_foiarequests.json', 'test_foiacommunications.json',
                'test_foiafiles.json', 'tags.json', 'taggit.json', 'tagged_item_base.json']

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
                    kwargs={'state_slug': self.state.slug, 'fed_slug': self.state.parent.slug}))

    def test_jurisdiction_legal(self):
        """Test Jurisdiction model's legal method"""
        nose.tools.eq_(self.state.legal(), 'MA')
        nose.tools.eq_(self.local.legal(), 'MA')

    def test_jurisdiction_get_days(self):
        """Test Jurisdiction model's get days method"""
        nose.tools.eq_(self.state.get_days(), 10)
        nose.tools.eq_(self.local.get_days(), 10)

    def test_exemptions(self):
        """Test the RequestHelper exemption mixin method with Jurisdictions"""

        nose.tools.eq_(list(self.state.exemptions()),
                [{'tags__name': u'exemption 42', 'count': 1},
                 {'tags__name': u'exemption x', 'count': 2}])

    def test_interesting_requests(self):
        """Test the RequestHelper interesting requests mixin method with Jurisdictions"""
        # pylint: disable=bad-whitespace

        nose.tools.eq_(self.state.interesting_requests(),
           [
            {'headline': 'Most Recently Completed Request', 'req': FOIARequest.objects.get(pk=10)},
            {'headline': 'Oldest Overdue Request',          'req': FOIARequest.objects.get(pk=15)},
            {'headline': 'Most Viewed Request',             'req': FOIARequest.objects.get(pk=17)},
           ])

    def test_average_response_time(self):
        """Test the RequestHelper average response time mixin method with Jurisdictions"""

        nose.tools.eq_(self.state.average_response_time(), 12)
        nose.tools.eq_(self.local.average_response_time(), 0)

    def test_total_pages(self):
        """Test the RequestHelper total pages mixin method with Jurisdictions"""

        nose.tools.eq_(self.state.total_pages(), 24)
        nose.tools.eq_(self.local.total_pages(), 0)
