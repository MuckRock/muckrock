"""
Tests the notification application.
"""

from django.test import TestCase

import actstream
import logging
import nose.tools

from muckrock import factories
from muckrock.notification.models import DailyNotification

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

class TestDailyNotification(TestCase):
    """Tests the daily email notification object. It extends Django's built-in email classes."""
    def setUp(self):
        self.user = factories.UserFactory()

    def test_init(self):
        """The email should create when given a User."""
        ok_(DailyNotification(self.user))

    @raises(TypeError)
    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        DailyNotification()

    def test_send_no_notifications(self):
        """The email shouldn't send if there's no notifications."""
        email = DailyNotification(self.user)
        eq_(email.send(), 0)

    def test_send_notification(self):
        """The email should send if there are notifications."""
        # generate an action on an actor the user follows
        other_user = factories.UserFactory()
        actstream.actions.follow(self.user, other_user)
        actstream.action.send(other_user, verb='acted')
        # generate the email, which should contain the generated action
        email = DailyNotification(self.user)
        logging.debug(email.notification_count)
        eq_(email.send(), 1)
