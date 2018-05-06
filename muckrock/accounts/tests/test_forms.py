"""
Tests accounts forms
"""

# Django
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

# Third Party
from mock import patch
from nose.tools import assert_false, assert_true, eq_, ok_

# MuckRock
from muckrock.accounts.forms import (
    BuyRequestForm,
    EmailSettingsForm,
    RegisterForm,
)
from muckrock.factories import ProfileFactory, UserFactory


class TestEmailSettingsForm(TestCase):
    """Users should be able to modify their email settings."""

    def setUp(self):
        """Set up tests"""
        self.profile = ProfileFactory()
        self.data = {
            'email_pref': self.profile.email_pref,
            'use_autologin': self.profile.use_autologin,
            'email': self.profile.user.email
        }
        self.form = EmailSettingsForm

    @patch('stripe.Customer.retrieve')
    @patch('muckrock.message.tasks.email_change.delay')
    def test_email_normal(self, mock_notify, mock_stripe):
        """Changing email normally should succeed"""
        # pylint: disable=unused-argument
        old_email = self.profile.user.email
        new_email = 'new@example.com'
        self.data['email'] = new_email
        form = self.form(self.data, instance=self.profile)
        assert_true(form.is_valid())
        eq_(form.clean_email(), new_email)
        form.save()
        mock_notify.assert_called_once_with(self.profile.user, old_email)

    @patch('muckrock.message.tasks.email_change.delay')
    def test_email_same(self, mock_notify):
        """Keeping email the same should succeed"""
        form = self.form(self.data, instance=self.profile)
        assert_true(form.is_valid())
        eq_(form.clean_email(), self.profile.user.email)
        form.save()
        mock_notify.assert_not_called()

    def test_email_conflict(self):
        """Trying to use an already taken email should fail"""
        other_user = UserFactory()
        self.data['email'] = other_user.email
        form = self.form(self.data, instance=self.profile)
        assert_false(form.is_valid())


class TestRegistrationForm(TestCase):
    """New users should be created using a registration form."""

    def setUp(self):
        self.user = UserFactory()
        self.form = RegisterForm

    def test_unique_username(self):
        """Username should be unique (case insensitive)"""
        existing_username = self.user.username
        data = {
            'username': existing_username,
            'email': 'different@example.com',
            'first_name': 'Adam',
            'last_name': 'Smith',
            'password1': 'password',
            'password2': 'password'
        }
        form = self.form(data)
        assert_false(form.is_valid())

    def test_unique_email(self):
        """Email should be unique (case insensitive)"""
        existing_email = self.user.email
        data = {
            'username': 'different',
            'email': existing_email,
            'first_name': 'Adam',
            'last_name': 'Smith',
            'password1': 'password',
            'password2': 'password'
        }
        form = self.form(data)
        assert_false(form.is_valid())


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
        eq_(form._get_price(19), 19 * 500)
        eq_(form._get_price(20), 20 * 300)

    def test_get_price_basic(self):
        """Test getting the price for basic users"""
        user = UserFactory(profile__acct_type='basic')
        form = BuyRequestForm(user=user)
        eq_(form._get_price(19), 19 * 500)
        eq_(form._get_price(20), 20 * 400)
