"""
Tests accounts models
"""

# Django
from django.test import TestCase

# Third Party
from mock import Mock, patch
from nose.tools import assert_false, assert_true, eq_, ok_

# MuckRock
from muckrock.accounts.models import Notification
from muckrock.core.factories import (
    NotificationFactory,
    ProfileFactory,
    UserFactory,
)
from muckrock.core.utils import new_action
from muckrock.foia.factories import FOIARequestFactory

# Creates Mock items for testing methods that involve Stripe
#
# If you can't tell what's going on here, check out the Profile
# model methods that make calls with the stripe module then
# read up on how the Stripe API and mock module work.
#
# https://docs.python.org/dev/library/unittest.mock.html
# https://stripe.com/docs/api

mock_charge = Mock()
mock_charge.create = Mock()
mock_subscription = Mock()
mock_subscription.id = 'test-pro-subscription'
mock_subscription.save.return_value = mock_subscription
mock_subscription.delete.return_value = mock_subscription
mock_customer = Mock()
mock_customer.id = 'test-customer'
mock_customer.save.return_value = mock_customer
mock_customer.update_subscription.return_value = mock_subscription
mock_customer.cancel_subscription.return_value = mock_subscription
mock_customer.subscriptions.create.return_value = mock_subscription
mock_customer.subscriptions.retrieve.return_value = mock_subscription
mock_customer.subscriptions.data = [mock_subscription]
MockCustomer = Mock()
MockCustomer.create.return_value = mock_customer
MockCustomer.retrieve.return_value = mock_customer


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Charge', mock_charge)
class TestProfileUnit(TestCase):
    """Unit tests for profile model"""

    def setUp(self):
        self.profile = ProfileFactory(acct_type='pro',)

    def test_unicode(self):
        """Test profile model's __unicode__ method"""
        expected = "%s's Profile" % unicode(self.profile.user).capitalize()
        eq_(unicode(self.profile), expected)

    def _test_is_advanced(self):
        """Test whether the users are marked as advanced."""
        beta = ProfileFactory(acct_type='beta')
        proxy = ProfileFactory(acct_type='beta')
        admin = ProfileFactory(acct_type='admin')
        basic = ProfileFactory(acct_type='basic')
        # XXX active vs inactive is closest to free vs paid
        active_org_member = ProfileFactory(acct_type='basic')
        inactive_org_member = ProfileFactory(acct_type='basic')
        assert_true(self.profile.is_advanced())
        assert_true(beta.is_advanced())
        assert_true(proxy.is_advanced())
        assert_true(admin.is_advanced())
        assert_true(active_org_member.is_advanced())
        assert_false(basic.is_advanced())
        assert_false(inactive_org_member.is_advanced())

    def _test_multiple_requests(self):
        """Test how many of each request type you need"""
        # XXX redo how this is tested
        profile = ProfileFactory(
            monthly_requests=2,
            num_requests=3,
        )
        eq_(
            profile.multiple_requests(2),
            {
                'org': 1,
                'monthly': 1,
                'regular': 0,
                'extra': 0,
            },
        )
        eq_(
            profile.multiple_requests(7),
            {
                'org': 1,
                'monthly': 2,
                'regular': 3,
                'extra': 1,
            },
        )
        profile = ProfileFactory(
            monthly_requests=2,
            num_requests=0,
        )
        eq_(
            profile.multiple_requests(2),
            {
                'org': 0,
                'monthly': 2,
                'regular': 0,
                'extra': 0,
            },
        )
        eq_(
            profile.multiple_requests(7),
            {
                'org': 0,
                'monthly': 2,
                'regular': 0,
                'extra': 5,
            },
        )


class TestNotifications(TestCase):
    """Notifications connect actions to users and contain a read state."""

    def setUp(self):
        self.user = UserFactory()
        self.action = new_action(self.user, 'acted')
        self.notification = NotificationFactory()

    def test_create_notification(self):
        """Create a notification with a user and an action."""
        notification = Notification.objects.create(
            user=self.user, action=self.action
        )
        ok_(notification, 'Notification object should create without error.')
        ok_(
            isinstance(notification, Notification),
            'Object should be a Notification.'
        )
        ok_(
            notification.read is not True,
            'Notification sould be unread by default.'
        )

    def test_mark_read(self):
        """Notifications should be markable as read if unread and unread if read."""
        self.notification.mark_read()
        ok_(
            self.notification.read is True,
            'Notification should be marked as read.'
        )
        self.notification.mark_unread()
        ok_(
            self.notification.read is not True,
            'Notification should be marked as unread.'
        )

    def test_for_user(self):
        """Notifications should be filterable by a single user."""
        user_notification = NotificationFactory(user=self.user)
        user_notifications = Notification.objects.for_user(self.user)
        ok_(
            user_notification in user_notifications,
            'A notification for the user should be in the set returned.'
        )
        ok_(
            self.notification not in user_notifications,
            'A notification for another user should not be in the set returned.'
        )

    def test_for_model(self):
        """Notifications should be filterable by a model type."""
        foia = FOIARequestFactory()
        _action = new_action(UserFactory(), 'submitted', target=foia)
        object_notification = NotificationFactory(
            user=self.user, action=_action
        )
        model_notifications = Notification.objects.for_model(foia)
        ok_(
            object_notification in model_notifications,
            'A notification for the model should be in the set returned.'
        )
        ok_(
            self.notification not in model_notifications,
            'A notification not including the model should not be in the set returned.'
        )

    def test_for_object(self):
        """Notifications should be filterable by a single object."""
        foia = FOIARequestFactory()
        _action = new_action(UserFactory(), 'submitted', target=foia)
        object_notification = NotificationFactory(
            user=self.user, action=_action
        )
        object_notifications = Notification.objects.for_object(foia)
        ok_(
            object_notification in object_notifications,
            'A notification for the object should be in the set returned.'
        )
        ok_(
            self.notification not in object_notifications,
            'A notification not including the object should not be in the set returned.'
        )

    def test_get_unread(self):
        """Notifications should be filterable by their unread status."""
        self.notification.mark_unread()
        ok_(
            self.notification in Notification.objects.get_unread(),
            'Unread notifications should be in the set returned.'
        )
        self.notification.mark_read()
        ok_(
            self.notification not in Notification.objects.get_unread(),
            'Read notifications should not be in the set returned.'
        )
