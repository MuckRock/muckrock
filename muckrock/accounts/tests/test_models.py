"""
Tests accounts models
"""

from django.conf import settings
from django.test import TestCase

from datetime import datetime, date, timedelta
from mock import Mock, patch, ANY
from nose.tools import ok_, eq_, assert_true, assert_false, raises, nottest

from muckrock.accounts.models import Notification
from muckrock import factories
from muckrock.utils import new_action, get_stripe_token

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
        self.profile = factories.ProfileFactory(monthly_requests=25, acct_type='pro')

    def test_unicode(self):
        """Test profile model's __unicode__ method"""
        expected = "%s's Profile" % unicode(self.profile.user).capitalize()
        eq_(unicode(self.profile), expected)

    def test_is_advanced(self):
        """Test whether the users are marked as advanced."""
        beta = factories.ProfileFactory(acct_type='beta')
        proxy = factories.ProfileFactory(acct_type='beta')
        admin = factories.ProfileFactory(acct_type='admin')
        basic = factories.ProfileFactory(acct_type='basic')
        active_org = factories.OrganizationFactory(active=True)
        inactive_org = factories.OrganizationFactory(active=False)
        active_org_member = factories.ProfileFactory(acct_type='basic', organization=active_org)
        inactive_org_member = factories.ProfileFactory(acct_type='basic', organization=inactive_org)
        assert_true(self.profile.is_advanced())
        assert_true(beta.is_advanced())
        assert_true(proxy.is_advanced())
        assert_true(admin.is_advanced())
        assert_true(active_org_member.is_advanced())
        assert_false(basic.is_advanced())
        assert_false(inactive_org_member.is_advanced())

    def test_monthly_requests(self):
        """Normal get number requests just returns the current value"""
        eq_(self.profile.get_monthly_requests(), self.profile.monthly_requests)

    def test_monthly_requests_refresh(self):
        """Get number requests resets the number of requests if its been over a month"""
        self.profile.date_update = datetime.now() - timedelta(32)
        monthly_requests = settings.MONTHLY_REQUESTS[self.profile.acct_type]
        eq_(self.profile.get_monthly_requests(), monthly_requests)
        eq_(self.profile.date_update, date.today())

    def test_make_request_refresh(self):
        """Make request resets count if it has been more than a month"""
        self.profile.date_update = date.today() - timedelta(32)
        assert_true(self.profile.make_request())

    def test_make_request_pass_monthly(self):
        """Make request call decrements number of monthly requests"""
        num_requests = self.profile.monthly_requests
        self.profile.make_request()
        eq_(self.profile.monthly_requests, num_requests - 1)

    def test_make_request_pass(self):
        """Make request call decrements number of requests if out of monthly requests"""
        # pylint:disable=no-self-use
        num_requests = 10
        profile = factories.ProfileFactory(num_requests=num_requests)
        profile.make_request()
        eq_(profile.num_requests, num_requests - 1)

    def test_make_request_fail(self):
        """If out of requests, make request returns false"""
        # pylint:disable=no-self-use
        profile = factories.ProfileFactory(num_requests=0)
        profile.date_update = date.today()
        assert_false(profile.make_request())

    def test_customer(self):
        """Test accessing the profile's Stripe customer"""
        ok_(not self.profile.customer_id)
        customer = self.profile.customer()
        ok_(MockCustomer.create.called,
            'If no customer exists, it should be created.')
        eq_(customer, mock_customer)
        eq_(self.profile.customer_id, mock_customer.id,
            'The customer id should be saved so the customer can be retrieved.')
        customer = self.profile.customer()
        ok_(MockCustomer.retrieve.called,
            'After the customer exists, it should be retrieved for subsequent calls.')

    def test_pay(self):
        """Test making a payment"""
        token = 'token'
        amount = 100
        modified_amount = 105
        metadata = {
            'email': self.profile.user.email,
            'action': 'test-charge'
        }
        self.profile.pay(token, amount, metadata)
        mock_charge.create.assert_called_with(
            currency='usd',
            amount=modified_amount,
            metadata=metadata,
            source=token,
            idempotency_key=ANY,
            )

    def test_start_pro_subscription(self):
        """Test starting a pro subscription"""
        self.profile.start_pro_subscription()
        self.profile.refresh_from_db()
        ok_(mock_customer.subscriptions.create.called)
        eq_(self.profile.acct_type, 'pro')
        eq_(self.profile.subscription_id, mock_subscription.id)
        eq_(self.profile.date_update, date.today())
        eq_(self.profile.monthly_requests, settings.MONTHLY_REQUESTS.get('pro'))

    @raises(AttributeError)
    def test_start_pro_as_owner(self):
        """Organization owners shouldn't be able to start a pro subscription."""
        self.profile.subscription_id = 'test-org'
        self.profile.start_pro_subscription()

    def test_cancel_pro_subscription(self):
        """Test ending a pro subscription"""
        self.profile.start_pro_subscription()
        self.profile.cancel_pro_subscription()
        self.profile.refresh_from_db()
        ok_(mock_subscription.delete.called)
        eq_(self.profile.acct_type, 'basic')
        ok_(not self.profile.subscription_id)
        eq_(self.profile.monthly_requests, settings.MONTHLY_REQUESTS.get('basic'))

    def test_cancel_pro_missing_sub(self):
        """Test cancelling a pro subscription without a subscription_id."""
        self.profile.customer().subscriptions.data = []
        self.profile.acct_type = 'pro'
        self.profile.save()
        ok_(not self.profile.subscription_id)
        self.profile.cancel_pro_subscription()
        self.profile.refresh_from_db()
        ok_(self.profile.acct_type, 'basic')

    def test_cancel_legacy_subscription(self):
        """Test ending a pro subscription when missing a subscription ID"""
        # pylint:disable=no-self-use
        pro_profile = factories.ProfileFactory(acct_type='basic',
                                     monthly_requests=settings.MONTHLY_REQUESTS.get('pro'))
        ok_(not pro_profile.subscription_id)
        pro_profile.cancel_pro_subscription()
        eq_(pro_profile.acct_type, 'basic')
        eq_(pro_profile.monthly_requests, settings.MONTHLY_REQUESTS.get('basic'))


class TestStripeIntegration(TestCase):
    """
    Tests Stripe integration and error handling.

    These tests are disabled by default because they communicate with Stripe's backend.
    If the methods tested here are changed, make sure to disable the @nottest decorator.
    After testing your changes locally, enable the decorator again.
    """
    def setUp(self):
        self.profile = factories.ProfileFactory()

    @nottest
    def test_pay(self):
        """Test making a payment"""
        token = get_stripe_token()
        metadata = {
            'email': self.profile.user.email,
            'action': 'test-charge'
        }
        self.profile.pay(token, 100, metadata)

    @nottest
    def test_customer(self):
        """Test accessing the profile's Stripe customer"""
        ok_(not self.profile.customer_id)
        self.profile.customer()
        ok_(self.profile.customer_id,
            'The customer id should be saved so the customer can be retrieved later.')

    @nottest
    def test_subscription(self):
        """Test starting a subscription"""
        customer = self.profile.customer()
        customer.sources.create(source=get_stripe_token())
        customer.save()
        self.profile.start_pro_subscription()
        self.profile.cancel_pro_subscription()


class TestNotifications(TestCase):
    """Notifications connect actions to users and contain a read state."""
    def setUp(self):
        self.user = factories.UserFactory()
        self.action = new_action(self.user, 'acted')
        self.notification = factories.NotificationFactory()

    def test_create_notification(self):
        """Create a notification with a user and an action."""
        notification = Notification.objects.create(user=self.user, action=self.action)
        ok_(notification, 'Notification object should create without error.')
        ok_(isinstance(notification, Notification), 'Object should be a Notification.')
        ok_(notification.read is not True, 'Notification sould be unread by default.')

    def test_mark_read(self):
        """Notifications should be markable as read if unread and unread if read."""
        self.notification.mark_read()
        ok_(self.notification.read is True, 'Notification should be marked as read.')
        self.notification.mark_unread()
        ok_(self.notification.read is not True, 'Notification should be marked as unread.')

    def test_for_user(self):
        """Notifications should be filterable by a single user."""
        user_notification = factories.NotificationFactory(user=self.user)
        user_notifications = Notification.objects.for_user(self.user)
        ok_(user_notification in user_notifications,
            'A notification for the user should be in the set returned.')
        ok_(self.notification not in user_notifications,
            'A notification for another user should not be in the set returned.')

    def test_for_model(self):
        """Notifications should be filterable by a model type."""
        foia = factories.FOIARequestFactory()
        _action = new_action(factories.UserFactory(), 'submitted', target=foia)
        object_notification = factories.NotificationFactory(user=self.user, action=_action)
        model_notifications = Notification.objects.for_model(foia)
        ok_(object_notification in model_notifications,
            'A notification for the model should be in the set returned.')
        ok_(self.notification not in model_notifications,
            'A notification not including the model should not be in the set returned.')

    def test_for_object(self):
        """Notifications should be filterable by a single object."""
        foia = factories.FOIARequestFactory()
        _action = new_action(factories.UserFactory(), 'submitted', target=foia)
        object_notification = factories.NotificationFactory(user=self.user, action=_action)
        object_notifications = Notification.objects.for_object(foia)
        ok_(object_notification in object_notifications,
            'A notification for the object should be in the set returned.')
        ok_(self.notification not in object_notifications,
            'A notification not including the object should not be in the set returned.')

    def test_get_unread(self):
        """Notifications should be filterable by their unread status."""
        self.notification.mark_unread()
        ok_(self.notification in Notification.objects.get_unread(),
            'Unread notifications should be in the set returned.')
        self.notification.mark_read()
        ok_(self.notification not in Notification.objects.get_unread(),
            'Read notifications should not be in the set returned.')
