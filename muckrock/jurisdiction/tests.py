"""
Tests for Jurisdiction application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase

from datetime import date, timedelta
import nose.tools

from .factories import StateJurisdictionFactory, LocalJurisdictionFactory
from muckrock.factories import FOIARequestFactory, FOIAFileFactory

class TestJurisdictionUnit(TestCase):
    """Unit tests for Jurisdictions"""
    def setUp(self):
        """Set up tests"""
        self.state = StateJurisdictionFactory()
        self.local = LocalJurisdictionFactory(parent=self.state)

    def test_jurisdiction_unicode(self):
        """Test Jurisdiction model's __unicode__ method"""
        nose.tools.eq_(unicode(self.state), u'Massachusetts')
        nose.tools.eq_(unicode(self.local), u'Boston, MA')

    def test_jurisdiction_url(self):
        """Test Jurisdiction model's get_absolute_url method"""
        nose.tools.eq_(self.state.get_absolute_url(),
            reverse('jurisdiction-detail', kwargs={
                'state_slug': self.state.slug,
                'fed_slug': self.state.parent.slug}
            )
        )

    def test_jurisdiction_legal(self):
        """Test Jurisdiction model's legal method"""
        nose.tools.eq_(self.state.legal(), 'MA')
        nose.tools.eq_(self.local.legal(), 'MA')

    def test_jurisdiction_get_days(self):
        """Test Jurisdiction model's get days method"""
        nose.tools.eq_(self.state.get_days(), 20)
        nose.tools.eq_(self.local.get_days(), 20)

    def test_exemptions(self):
        """
        Jurisdictions should report the exemptions on their requests.
        State jurisdictions should include exemptions on their local jurisdictions.
        """
        foia1 = FOIARequestFactory(jurisdiction=self.local)
        foia2 = FOIARequestFactory(jurisdiction=self.state)
        for tag in [u'exemption 42', u'exemption x']:
            foia1.tags.add(tag)
        foia2.tags.add(u'exemption x')
        nose.tools.eq_(list(self.state.exemptions()),
                [{'tags__name': u'exemption 42', 'count': 1},
                 {'tags__name': u'exemption x', 'count': 2}])
        nose.tools.eq_(list(self.local.exemptions()),
                [{'tags__name': u'exemption 42', 'count': 1},
                 {'tags__name': u'exemption x', 'count': 1}])

    def test_average_response_time(self):
        """
        Jurisdictions should report their average response time.
        State jurisdictions should include avg. response time of their local jurisdictions.
        """
        today = date.today()
        state_duration = 12
        local_duration = 6
        FOIARequestFactory(
            jurisdiction=self.state,
            date_done=today,
            date_submitted=today-timedelta(state_duration)
        )
        FOIARequestFactory(
            jurisdiction=self.local,
            date_done=today,
            date_submitted=today-timedelta(local_duration)
        )
        nose.tools.eq_(self.state.average_response_time(), (local_duration + state_duration)/2)
        nose.tools.eq_(self.local.average_response_time(), local_duration)

    def test_total_pages(self):
        """
        Jurisdictions should report the pages returned across their requests.
        State jurisdictions should include pages from their local jurisdictions.
        """
        page_count = 10
        local_foia = FOIARequestFactory(jurisdiction=self.local)
        state_foia = FOIARequestFactory(jurisdiction=self.state)
        local_foia.files.add(FOIAFileFactory(pages=page_count))
        state_foia.files.add(FOIAFileFactory(pages=page_count))
        nose.tools.eq_(self.local.total_pages(), page_count)
        nose.tools.eq_(self.state.total_pages(), 2*page_count)
