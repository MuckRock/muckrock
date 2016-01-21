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
        self.interval = relativedelta(days=1)

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
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, other_user)
        actstream.action.send(other_user, verb='acted')
        # generate the email, which should contain the generated action
        email = self.digest(self.user)
        ok_(email.activity['count'] > 0, 'There should be activity.')
        eq_(email.send(), 1, 'The email should send.')

    def test_notification_composition(self):
        """The email should be composed of updates to requests I own and things I follow."""
        # lets create a FOIA to belong to our user
        foia = factories.FOIARequestFactory(user=self.user)
        # lets have this FOIA do some things
        actstream.action.send(foia, verb='created')
        # lets also create an agency to act upon our FOIA
        agency = factories.AgencyFactory()
        actstream.action.send(agency, verb='rejected', action_object=foia)
        # lets also have the user follow somebody
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, other_user, actor_only=False)
        # lets generate some actions on behalf of this other user
        actstream.action.send(other_user, verb='acted')
        actstream.action.send(agency, verb='sent an email', target=other_user)
        email = self.digest(self.user)
        logging.info(email.message())


class TestDigestIntervals(TestCase):
    """All digests should behave the same, except for their interval"""
    def setUp(self):
        self.user = factories.UserFactory()

    def test_hourly(self):
        digest = digests.HourlyDigest(self.user)
        eq_(digest.interval, relativedelta(hours=1))

    def test_daily(self):
        digest = digests.DailyDigest(self.user)
        eq_(digest.interval, relativedelta(days=1))

    def test_weekly(self):
        digest = digests.WeeklyDigest(self.user)
        eq_(digest.interval, relativedelta(weeks=1))

    def test_monthly(self):
        digest = digests.MonthlyDigest(self.user)
        eq_(digest.interval, relativedelta(months=1))
