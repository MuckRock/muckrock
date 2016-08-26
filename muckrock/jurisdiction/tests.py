"""
Tests for Jurisdiction application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase
import nose.tools

from datetime import date, timedelta

from muckrock.factories import (
        StateJurisdictionFactory,
        LocalJurisdictionFactory,
        FOIARequestFactory,
        FOIAFileFactory,
        )

# allow methods that could be functions and too many public methods in tests
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=bad-continuation

class TestJurisdictionUnit(TestCase):
    """Unit tests for Jurisdictions"""

    def test_jurisdiction_unicode(self):
        """Test Jurisdiction model's __unicode__ method"""
        state = StateJurisdictionFactory(name='Massachusetts', abbrev='MA')
        local = LocalJurisdictionFactory(name='Boston', parent=state)
        nose.tools.eq_(unicode(state), u'Massachusetts')
        nose.tools.eq_(unicode(local), u'Boston, MA')

    def test_jurisdiction_url(self):
        """Test Jurisdiction model's get_absolute_url method"""
        state = StateJurisdictionFactory()
        nose.tools.eq_(state.get_absolute_url(),
            reverse('jurisdiction-detail',
                    kwargs={
                        'state_slug': state.slug,
                        'fed_slug': state.parent.slug}))

    def test_jurisdiction_legal(self):
        """Test Jurisdiction model's legal method"""
        state = StateJurisdictionFactory(name='Massachusetts', abbrev='MA')
        local = LocalJurisdictionFactory(name='Boston', parent=state)
        nose.tools.eq_(state.legal(), 'MA')
        nose.tools.eq_(local.legal(), 'MA')

    def test_jurisdiction_get_days(self):
        """Test Jurisdiction model's get days method"""
        state = StateJurisdictionFactory(days=10)
        local = LocalJurisdictionFactory(parent=state, days=None)
        nose.tools.eq_(state.get_days(), 10)
        nose.tools.eq_(local.get_days(), 10)

    def test_average_response_time(self):
        """Test the RequestHelper average response time mixin method with Jurisdictions"""
        state = StateJurisdictionFactory()
        local = LocalJurisdictionFactory()
        FOIARequestFactory(
                jurisdiction=state,
                date_submitted=date.today() - timedelta(18),
                date_done=date.today())
        FOIARequestFactory(
                jurisdiction=state,
                date_submitted=date.today() - timedelta(6),
                date_done=date.today())

        nose.tools.eq_(state.average_response_time(), 12)
        nose.tools.eq_(local.average_response_time(), 0)

    def test_total_pages(self):
        """Test the RequestHelper total pages mixin method with Jurisdictions"""
        state = StateJurisdictionFactory()
        local = LocalJurisdictionFactory()
        FOIAFileFactory(
                foia__jurisdiction=state,
                pages=18)
        FOIAFileFactory(
                foia__jurisdiction=state,
                pages=6)

        nose.tools.eq_(state.total_pages(), 24)
        nose.tools.eq_(local.total_pages(), 0)
