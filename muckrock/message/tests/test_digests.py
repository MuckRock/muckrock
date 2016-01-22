"""
Test the message digests.
These will tell us if digests are
correctly grabbing site activity.
"""

from django.test import TestCase

import actstream
from dateutil.relativedelta import relativedelta
import logging
import nose.tools

from muckrock import factories
from muckrock.message import digests

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

class TestDailyDigest(TestCase):
    """Tests the daily digest notification object. It extends Django's built-in email classes."""
    def setUp(self):
        self.user = factories.UserFactory()
        self.digest = digests.DailyDigest

    def test_init(self):
        """The email should create when given a User."""
        ok_(self.digest(self.user))

    @raises(TypeError)
    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        self.digest(None)

    def test_send_no_notifications(self):
        """The email shouldn't send if there's no notifications."""
        email = self.digest(self.user)
        eq_(email.activity['count'], 0, 'There should be no activity.')
        eq_(email.send(), 0, 'The email should not send.')

    def test_send_notification(self):
        """The email should send if there are notifications."""
        # generate an action on an actor the user follows
        foia = factories.FOIARequestFactory()
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, foia, actor_only=False)
        actstream.action.send(other_user, verb='submitted', action_object=foia)
        # generate the email, which should contain the generated action
        email = self.digest(self.user)
        eq_(email.activity['count'], 1, 'There should be activity.')
        eq_(email.send(), 1, 'The email should send.')

    def test_digest_user_requests(self):
        """Digests should include information on requests I own."""
        # generate an action on a request the user owns
        foia = factories.FOIARequestFactory(user=self.user)
        agency = factories.AgencyFactory()
        actstream.action.send(agency, verb='rejected', action_object=foia)
        actstream.action.send(self.user, verb='followed up on', action_object=foia)
        # generate the email, which should contain the generated action
        email = self.digest(self.user)
        eq_(email.activity['count'], 1, 'There should be activity that is not user initiated.')
        eq_(email.activity['requests']['mine'].first().actor, agency, 'User activity should be excluded.')
        eq_(email.send(), 1, 'The email should send.')

    def test_digest_follow_requests(self):
        """Digests should include information on requests I follow."""
        # generate an action on a request the user owns
        other_user = factories.UserFactory()
        foia = factories.FOIARequestFactory(user=other_user)
        actstream.actions.follow(self.user, foia, actor_only=False)
        agency = factories.AgencyFactory()
        actstream.action.send(agency, verb='rejected', action_object=foia)
        # generate the email, which should contain the generated action
        email = self.digest(self.user)
        eq_(email.activity['count'], 1, 'There should be activity.')
        eq_(email.activity['requests']['following'].first().actor, agency)
        eq_(email.send(), 1, 'The email should send.')


class TestDigestIntervals(TestCase):
    """All digests should behave the same, except for their interval"""
    def setUp(self):
        self.user = factories.UserFactory()

    def test_hourly(self):
        """1 hour interval"""
        digest = digests.HourlyDigest(self.user)
        eq_(digest.interval, relativedelta(hours=1))

    def test_daily(self):
        """1 day interval"""
        digest = digests.DailyDigest(self.user)
        eq_(digest.interval, relativedelta(days=1))

    def test_weekly(self):
        """1 week interval"""
        digest = digests.WeeklyDigest(self.user)
        eq_(digest.interval, relativedelta(weeks=1))

    def test_monthly(self):
        """1 month interval"""
        digest = digests.MonthlyDigest(self.user)
        eq_(digest.interval, relativedelta(months=1))
