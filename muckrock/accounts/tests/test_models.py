"""
Tests accounts models
"""

from django.test import TestCase

from datetime import datetime, date, timedelta
from mock import Mock, patch
from nose.tools import ok_, eq_, assert_true, assert_false, raises, nottest
import stripe

from muckrock.factories import ProfileFactory
from muckrock.settings import MONTHLY_REQUESTS
from muckrock.utils import get_stripe_token

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
        self.profile = ProfileFactory(monthly_requests=25, acct_type='pro')

    def test_unicode(self):
        """Test profile model's __unicode__ method"""
        expected = "%s's Profile" % unicode(self.profile.user).capitalize()
        eq_(unicode(self.profile), expected)

    def test_get_monthly_requests(self):
        """Normal get number requests just returns the current value"""
        eq_(self.profile.get_monthly_requests(), self.profile.monthly_requests)

    def test_get_monthly_requests_refresh(self):
        """Get number requests resets the number of requests if its been over a month"""
        self.profile.date_update = datetime.now() - timedelta(32)
        monthly_requests = MONTHLY_REQUESTS[self.profile.acct_type]
        eq_(self.profile.get_monthly_requests(), monthly_requests)
        eq_(self.profile.date_update.date(), date.today())

    def test_make_request_refresh(self):
        """Make request resets count if it has been more than a month"""
        self.profile.date_update = datetime.now() - timedelta(32)
        assert_true(self.profile.make_request())

    def test_make_request_pass_monthly(self):
        """Make request call decrements number of monthly requests"""
        num_requests = self.profile.monthly_requests
        self.profile.make_request()
        eq_(self.profile.monthly_requests, num_requests - 1)

    def test_make_request_pass(self):
        """Make request call decrements number of requests if out of monthly requests"""
        num_requests = 10
        profile = ProfileFactory(num_requests=num_requests)
        profile.make_request()
        eq_(profile.num_requests, num_requests - 1)

    def test_make_request_fail(self):
        """If out of requests, make request returns false"""
        profile = ProfileFactory(num_requests=0)
        profile.date_update = datetime.now()
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
        metadata = {
            'email': self.profile.user.email,
            'action': 'test-charge'
        }
        self.profile.pay('token', 100, metadata)
        ok_(mock_charge.create.called)

    def test_start_pro_subscription(self):
        """Test starting a pro subscription"""
        self.profile.start_pro_subscription()
        self.profile.refresh_from_db()
        ok_(mock_customer.subscriptions.create.called)
        eq_(self.profile.acct_type, 'pro')
        eq_(self.profile.subscription_id, mock_subscription.id)
        eq_(self.profile.date_update.today(), date.today())
        eq_(self.profile.monthly_requests, MONTHLY_REQUESTS.get('pro'))

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
        eq_(self.profile.monthly_requests, MONTHLY_REQUESTS.get('basic'))

    def test_cancel_legacy_subscription(self):
        """Test ending a pro subscription when missing a subscription ID"""
        pro_profile = ProfileFactory(acct_type='basic',
                                     monthly_requests=MONTHLY_REQUESTS.get('pro'))
        ok_(not pro_profile.subscription_id)
        pro_profile.cancel_pro_subscription()
        eq_(pro_profile.acct_type, 'basic')
        eq_(pro_profile.monthly_requests, MONTHLY_REQUESTS.get('basic'))


class TestStripeIntegration(TestCase):
    """
    Tests Stripe integration and error handling.

    These tests are disabled by default because they communicate with Stripe's backend.
    If the methods tested here are changed, make sure to disable the @nottest decorator.
    After testing your changes locally, enable the decorator again.
    """
    def setUp(self):
        self.profile = ProfileFactory()

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
