"""
Tests the notification application.
"""

from django.test import TestCase

import nose.tools

from muckrock import factories
from muckrock.notification.models import DailyNotification

ok_ = nose.tools.ok_
raises = nose.tools.raises

class TestDailyNotification(TestCase):
    """Tests the daily email notification object."""
    def setUp(self):
        self.user = factories.UserFactory()

    def test_init(self):
        """The email should create when given a User."""
        ok_(DailyNotification(self.user))

    @raises(TypeError)
    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        DailyNotification()
