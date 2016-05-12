"""
Tests for Jurisdiction application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase

from datetime import date, timedelta
from nose.tools import eq_

from muckrock.jurisdiction import factories
from muckrock.factories import FOIARequestFactory, FOIAFileFactory

class TestJurisdictionUnit(TestCase):
    """Unit tests for Jurisdictions"""
    def setUp(self):
        """Set up tests"""
        self.federal = factories.FederalJurisdictionFactory()
        self.state = factories.StateJurisdictionFactory(parent=self.federal)
        self.local = factories.LocalJurisdictionFactory(parent=self.state)

    def test_jurisdiction_repr(self):
        """Test Jurisdiction model's __repr__ method"""
        pattern = '<Jurisdiction: %d>'
        eq_(self.federal.__repr__(), pattern % self.federal.pk)
        eq_(self.state.__repr__(), pattern % self.state.pk)
        eq_(self.local.__repr__(), pattern % self.local.pk)

    def test_jurisdiction_unicode(self):
        """Test Jurisdiction model's __unicode__ method"""
        eq_(unicode(self.federal), u'United States of America')
        eq_(unicode(self.state), u'Massachusetts')
        eq_(unicode(self.local), u'Boston, MA')

    def test_jurisdiction_url(self):
        """Test Jurisdiction model's get_absolute_url method"""
        eq_(self.local.get_absolute_url(),
            reverse('jurisdiction-detail', kwargs={
                'local_slug': self.local.slug,
                'state_slug': self.state.slug,
                'fed_slug': self.federal.slug}
            )
        )
        eq_(self.state.get_absolute_url(),
            reverse('jurisdiction-detail', kwargs={
                'state_slug': self.state.slug,
                'fed_slug': self.federal.slug}
            )
        )
        eq_(self.federal.get_absolute_url(),
            reverse('jurisdiction-detail', kwargs={
                'fed_slug': self.federal.slug}
            )
        )

    def test_jurisdiction_legal(self):
        """Local jurisdictions should return state law"""
        eq_(self.federal.legal(), self.federal.abbrev)
        eq_(self.state.legal(), self.state.abbrev)
        eq_(self.local.legal(), self.state.abbrev)
        eq_(self.federal.get_law_name(), self.federal.law_name)
        eq_(self.state.get_law_name(), self.state.law_name)
        eq_(self.local.get_law_name(), self.state.law_name)

    def test_get_day_type(self):
        """Local jurisdictions should return state day type"""
        eq_(self.federal.get_day_type(), 'business')
        eq_(self.state.get_day_type(), 'business')
        eq_(self.local.get_day_type(), 'business')

    def test_jurisdiction_get_days(self):
        """Local jurisdictions should return state days"""
        eq_(self.federal.get_days(), self.federal.days)
        eq_(self.state.get_days(), self.state.days)
        eq_(self.local.get_days(), self.state.days)

    def test_jurisdiction_get_intro(self):
        """Local jurisdictions should return the state intro."""
        eq_(self.federal.get_intro(), self.federal.intro)
        eq_(self.state.get_intro(), self.state.intro)
        eq_(self.local.get_intro(), self.state.intro)

    def test_jurisdiction_get_waiver(self):
        """Local jurisdictions should return the state waiver."""
        eq_(self.federal.get_waiver(), self.federal.waiver)
        eq_(self.state.get_waiver(), self.state.waiver)
        eq_(self.local.get_waiver(), self.state.waiver)

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
        eq_(list(self.state.exemptions()),
                [{'tags__name': u'exemption 42', 'count': 1},
                 {'tags__name': u'exemption x', 'count': 2}])
        eq_(list(self.local.exemptions()),
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
        eq_(self.state.average_response_time(), (local_duration + state_duration)/2)
        eq_(self.local.average_response_time(), local_duration)

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
        eq_(self.local.total_pages(), page_count)
        eq_(self.state.total_pages(), 2*page_count)
