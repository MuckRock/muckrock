"""
Tests accounts forms
"""

# Django
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

# Third Party
from nose.tools import assert_false, eq_, ok_

# MuckRock
from muckrock.accounts.forms import BuyRequestForm
from muckrock.core.factories import UserFactory


class TestBuyRequestForm(TestCase):
    """A form to buy requests"""

    # pylint: disable=protected-access

    def test_init_anonymous_good(self):
        """Test initial values and good minimum values for an anonymous user"""
        user = AnonymousUser()
        data = {
            'stripe_email': 'test@example.com',
            'stripe_token': 'token',
            'num_requests': 4,
        }
        form = BuyRequestForm(data, user=user)
        eq_(form.fields['stripe_email'].initial, None)
        eq_(form.fields['num_requests'].initial, 4)
        ok_(form.is_valid())

    def test_init_anonymous_bad(self):
        """Test initial values and bad minimum values for an anonymous user"""
        user = AnonymousUser()
        data = {
            'stripe_email': 'test@example.com',
            'stripe_token': 'token',
            'num_requests': 3,
        }
        form = BuyRequestForm(data, user=user)
        eq_(form.fields['stripe_email'].initial, None)
        eq_(form.fields['num_requests'].initial, 4)
        assert_false(form.is_valid())

    def test_init_authenticated_bad(self):
        """Test initial values and bad minimum values for an authenticated user"""
        user = UserFactory()
        data = {
            'stripe_email': user.email,
            'stripe_token': 'token',
            'num_requests': 3,
        }
        form = BuyRequestForm(data, user=user)
        eq_(form.fields['stripe_email'].initial, user.email)
        eq_(form.fields['num_requests'].initial, 4)
        assert_false(form.is_valid())

    def test_init_advanced_good(self):
        """Test initial values and good minimum values for an advanced user"""
        user = UserFactory(profile__acct_type='pro')
        data = {
            'stripe_email': user.email,
            'stripe_token': 'token',
            'num_requests': 1,
        }
        form = BuyRequestForm(data, user=user)
        eq_(form.fields['stripe_email'].initial, user.email)
        eq_(form.fields['num_requests'].initial, 1)
        ok_(form.is_valid())

    def test_init_advanced_bad(self):
        """Test initial values and bad minimum values for an advanced user"""
        user = UserFactory(profile__acct_type='pro')
        data = {
            'stripe_email': user.email,
            'stripe_token': 'token',
            'num_requests': 0,
        }
        form = BuyRequestForm(data, user=user)
        eq_(form.fields['stripe_email'].initial, user.email)
        eq_(form.fields['num_requests'].initial, 1)
        assert_false(form.is_valid())

    def test_get_price_advanced(self):
        """Test getting the price for advanced users"""
        user = UserFactory(profile__acct_type='pro')
        form = BuyRequestForm(user=user)
        eq_(form.get_price(19), 19 * 500)
        eq_(form.get_price(20), 20 * 300)

    def test_get_price_basic(self):
        """Test getting the price for basic users"""
        user = UserFactory(profile__acct_type='basic')
        form = BuyRequestForm(user=user)
        eq_(form.get_price(19), 19 * 500)
        eq_(form.get_price(20), 20 * 400)
