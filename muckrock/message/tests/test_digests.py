"""
Test the message digests.
These will tell us if digests are
correctly grabbing site activity.
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date
from unittest.mock import Mock, patch

# Third Party
import pytest
from actstream.actions import follow
from dateutil.relativedelta import relativedelta

# MuckRock
from muckrock.core.factories import (
    AgencyFactory,
    AnswerFactory,
    StatisticsFactory,
    UserFactory,
)
from muckrock.core.utils import new_action, notify
from muckrock.foia.factories import FOIARequestFactory
from muckrock.message import digests


class TestDailyDigest(TestCase):
    """Tests the ActivityDigest."""

    def setUp(self):
        self.user = UserFactory()
        self.digest = digests.ActivityDigest
        self.interval = relativedelta(days=1)

    def test_init(self):
        """The email should create when given a User."""
        assert self.digest(user=self.user, interval=self.interval)

    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        with pytest.raises(NotImplementedError):
            self.digest(user=None, interval=self.interval)

    def test_send_no_notifications(self):
        """The email shouldn't send if there's no notifications."""
        email = self.digest(user=self.user, interval=self.interval)
        assert email.activity["count"] == 0, "There should be no activity."
        assert email.send() == 0, "The email should not send."

    def test_send_notification(self):
        """The email should send if there are notifications."""
        # generate an action on an actor the user follows
        agency = AgencyFactory()
        foia = FOIARequestFactory(agency=agency)
        action = new_action(agency, "completed", target=foia)
        notify(self.user, action)
        # generate the email, which should contain the generated action
        email = self.digest(user=self.user, interval=self.interval)
        assert email.activity["count"] == 1, "There should be activity."
        assert email.send() == 1, "The email should send."

    def test_digest_follow_requests(self):
        """Digests should include information on requests I follow."""
        # generate an action on a request the user owns
        other_user = UserFactory()
        foia = FOIARequestFactory(composer__user=other_user)
        agency = AgencyFactory()
        action = new_action(agency, "rejected", target=foia)
        notify(self.user, action)
        # generate the email, which should contain the generated action
        email = self.digest(user=self.user, interval=self.interval)
        assert email.activity["count"] == 1, "There should be activity."
        assert email.send() == 1, "The email should send."


class TestStaffDigest(TestCase):
    """The Staff Digest updates us about the state of the website."""

    def setUp(self):
        self.user = UserFactory(is_staff=True)
        interval = relativedelta(days=1)
        yesterday = date.today() - interval
        day_before_yesterday = yesterday - interval
        week_before_yesterday = yesterday - relativedelta(weeks=1)
        month_before_yesterday = yesterday - relativedelta(months=1)

        StatisticsFactory(date=yesterday)
        StatisticsFactory(date=day_before_yesterday)
        StatisticsFactory(date=week_before_yesterday)
        StatisticsFactory(date=month_before_yesterday)

    @patch("muckrock.message.digests.Zenpy", Mock())
    def test_send(self):
        """The digest should send to staff members without errors."""
        digest = digests.StaffDigest(user=self.user)
        assert digest.send() == 1

    @patch("muckrock.message.digests.Zenpy", Mock())
    def test_not_staff(self):
        """The digest should not send to users who are not staff."""
        not_staff = UserFactory()
        digest = digests.StaffDigest(user=not_staff)
        assert digest.send() == 0
