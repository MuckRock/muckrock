"""
Tests for the sidebar application
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import timedelta

# Third Party
from mock import patch
from nose.tools import eq_

# MuckRock
from muckrock.factories import UserFactory
from muckrock.sidebar.context_processors import sidebar_broadcast
from muckrock.sidebar.models import Broadcast


class TestBroadcasts(TestCase):
    """Broadcasts display information to specific usergroups."""

    def setUp(self):
        self.user = UserFactory()
        text = u'Lorem ipsum dolor sit amet'
        self.broadcast = Broadcast.objects.create(
            context=self.user.profile.acct_type, text=text
        )

    def test_get_broadcast(self):
        """The broadcast corresponding to the user type should be returned."""
        broadcast = sidebar_broadcast(self.user)
        eq_(broadcast, self.broadcast.text)

    def test_stale_broadcast(self):
        """Broadcasts older than a week should be hidden."""
        # mock the utility function used to calculate the date updated
        # via http://devblog.kogan.com/testing-auto_now-datetime-fields-in-django/
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = self.broadcast.updated - timedelta(8)
            self.broadcast.save()
            broadcast = sidebar_broadcast(self.user)
            eq_(broadcast, '')
