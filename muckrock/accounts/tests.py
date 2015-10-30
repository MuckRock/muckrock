"""
Tests using nose for the accounts application
"""

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import TestCase

from datetime import datetime, date, timedelta
import json
import logging
from mock import MagicMock, Mock, patch
import nose.tools
import os
import stripe

from muckrock.accounts.models import Profile
from muckrock.accounts.forms import UserChangeForm, RegisterForm
from muckrock.factories import UserFactory, ProfileFactory
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed
from muckrock.settings import MONTHLY_REQUESTS, SITE_ROOT
from muckrock.utils import get_stripe_token

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

# allow long names, methods that could be functions and too many public methods in tests
# pylint: disable=invalid-name
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=no-member

# TODO Fully test Stripe integration

# Creates mock items for testing methods that involve Stripe
mock_charge = Mock()
mock_charge.create = Mock()
mock_subscription = Mock()
mock_subscription.id = 'test-pro-subscription'
mock_subscription.save.return_value = mock_subscription
mock_customer = Mock()
mock_customer.id = 'test-customer'
mock_customer.subscriptions.create.return_value = mock_subscription
mock_customer.subscriptions.retrieve.return_value = mock_subscription
MockCustomer = Mock()
MockCustomer.create.return_value = mock_customer
MockCustomer.retrieve.return_value = mock_customer

"""
mock_customer = Mock()
mock_customer.id = 'cus_2jPQblsYu5doOE'
mock_customer.active_card.last4 = '1234'
mock_customer.active_card.type = 'Visa'
MockCustomer = Mock()
MockCustomer.create.return_value = mock_customer
MockCustomer.retrieve.return_value = mock_customer
"""

class TestAccountFormsUnit(TestCase):
    """Unit tests for account forms"""
    def setUp(self):
        """Set up tests"""
        self.profile = ProfileFactory()
        self.form = UserChangeForm(instance=self.profile)

    def test_user_change_form_email_normal(self):
        """Changing email normally should succeed"""
        new_email = 'new@example.com'
        self.form.cleaned_data = {'email': new_email}
        nose.tools.eq_(self.form.clean_email(), new_email)

    def test_user_change_form_email_same(self):
        """Keeping email the same should succeed"""
        existing_email = self.profile.user.email
        self.form.cleaned_data = {'email': existing_email}
        nose.tools.eq_(self.form.clean_email(), existing_email)

    def test_user_change_form_email_conflict(self):
        """Trying to use an already taken email should fail"""
        other_user = UserFactory()
        self.form.cleaned_data = {'email': other_user.email}
        nose.tools.assert_raises(ValidationError, self.form.clean_email)

    def test_user_creation_form(self):
        """Create a new user - name/email should be unique (case insensitive)"""
        existing_username = self.profile.user.username
        existing_email = self.profile.user.email
        data = {
            'username': existing_username,
            'email': 'different@example.com',
            'first_name': 'Adam',
            'last_name': 'Smith',
            'password1': 'password',
            'password2': 'password'
        }
        form = RegisterForm(data)
        nose.tools.assert_false(form.is_valid())
        data = {
            'username': 'different',
            'email': existing_email,
            'first_name': 'Adam',
            'last_name': 'Smith',
            'password1': 'password',
            'password2': 'password'
        }
        form = RegisterForm(data)
        nose.tools.assert_false(form.is_valid())


class TestProfileUnit(TestCase):
    """Unit tests for profile model"""
    fixtures = ['test_users.json', 'test_profiles.json', 'test_stripeccs.json']
    def setUp(self):
        self.profile = ProfileFactory(monthly_requests=25, acct_type='pro')

    def test_unicode(self):
        """Test profile model's __unicode__ method"""
        expected = "%s's Profile" % unicode(self.profile.user).capitalize()
        nose.tools.eq_(unicode(self.profile), expected)

    def test_get_monthly_requests(self):
        """Normal get number requests just returns the current value"""
        nose.tools.eq_(self.profile.get_monthly_requests(), self.profile.monthly_requests)

    def test_get_monthly_requests_refresh(self):
        """Get number requests resets the number of requests if its been over a month"""
        self.profile.date_update = datetime.now() - timedelta(32)
        monthly_requests = MONTHLY_REQUESTS[self.profile.acct_type]
        nose.tools.eq_(self.profile.get_monthly_requests(), monthly_requests)
        nose.tools.eq_(self.profile.date_update.date(), date.today())

    def test_make_request_refresh(self):
        """Make request resets count if it has been more than a month"""
        self.profile.date_update = datetime.now() - timedelta(32)
        nose.tools.assert_true(self.profile.make_request())

    def test_make_request_pass_monthly(self):
        """Make request call decrements number of monthly requests"""
        num_requests = self.profile.monthly_requests
        self.profile.make_request()
        nose.tools.eq_(self.profile.monthly_requests, num_requests - 1)

    def test_make_request_pass(self):
        """Make request call decrements number of requests if out of monthly requests"""
        num_requests = 10
        profile = ProfileFactory(num_requests=num_requests)
        profile.make_request()
        nose.tools.eq_(profile.num_requests, num_requests - 1)

    def test_make_request_fail(self):
        """If out of requests, make request returns false"""
        profile = Profile.objects.get(pk=3)
        profile.date_update = datetime.now()
        nose.tools.assert_false(profile.make_request())

    @patch('stripe.Customer', MockCustomer)
    def test_customer(self):
        """Test accessing the profile's Stripe customer"""
        ok_(not self.profile.stripe_id)
        customer = self.profile.customer()
        ok_(MockCustomer.create.called,
            'If no customer exists, it should be created.')
        eq_(customer, mock_customer)
        eq_(self.profile.stripe_id, mock_customer.id,
            'The customer id should be saved so the customer can be retrieved.')
        customer = self.profile.customer()
        ok_(MockCustomer.retrieve.called,
            'After the customer exists, it should be retrieved for subsequent calls.')

    @patch('stripe.Charge', mock_charge)
    def test_pay(self):
        """Test making a payment"""
        self.profile.pay('token', 100, 'test charge')
        ok_(mock_charge.create.called)

    def test_start_pro_subscription(self):
        """Test starting a pro subscription"""
        ok_(False, 'Test unwritten.')

    def test_cancel_pro_subscription(self):
        """Test ending a pro subscription"""
        ok_(False, 'Test unwritten.')


class TestStripeIntegration(TestCase):
    """Tests stripe integration and error handling"""
    def setUp(self):
        self.profile = ProfileFactory()

    def test_pay(self):
        """Test making a payment"""
        token = get_stripe_token()
        self.profile.pay(token, 100, 'Test charge (muckrock.accounts.tests)')

    def test_customer(self):
        """Test accessing the profile's Stripe customer"""
        ok_(not self.profile.stripe_id)
        customer = self.profile.customer()
        ok_(self.profile.stripe_id,
            'The customer id should be saved so the customer can be retrieved later.')


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Charge', Mock())
class TestAccountFunctional(TestCase):
    """Functional tests for account"""
    fixtures = ['test_users.json', 'test_profiles.json', 'test_statistics.json']

    def setUp(self):
        """Set up tests"""
        mail.outbox = []

    # views
    def test_anon_views(self):
        """Test public views while not logged in"""
        # pylint: disable=bad-whitespace

        get_allowed(self.client,
            reverse('acct-profile', args=['adam']),
            ['profile/account.html', 'base_profile.html'])
        get_allowed(self.client,
            reverse('acct-login'),
            ['forms/account/login.html', 'forms/base_form.html'])
        get_allowed(self.client,
            reverse('acct-register'),
            ['forms/account/register.html', 'forms/base_form.html'])
        get_allowed(self.client,
            reverse('acct-register-free'),
            ['forms/account/register.html', 'forms/base_form.html'])
        get_allowed(self.client,
            reverse('acct-register-pro'),
            ['forms/account/subscription.html'])
        get_allowed(self.client,
            reverse('acct-reset-pw'),
            ['forms/account/pw_reset_part1.html', 'forms/base_form.html'])
        get_allowed(self.client,
            reverse('acct-logout'),
            ['front_page.html'])

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        # get/post authenticated pages while unauthenticated
        url_names = ['acct-my-profile', 'acct-update', 'acct-change-pw',
                     'acct-buy-requests']
        for url_name in url_names:
            get_post_unallowed(self.client, reverse(url_name))

    def test_login_view(self):
        """Test the login view"""

        # bad user name
        post_allowed_bad(self.client, reverse('acct-login'),
                         ['forms/account/login.html', 'forms/base_form.html'],
                         data={'username': 'nouser', 'password': 'abc'})
        # bad pw
        post_allowed_bad(self.client, reverse('acct-login'),
                         ['forms/account/login.html', 'forms/base_form.html'],
                         data={'username': 'adam', 'password': 'bad pw'})
        # succesful login
        post_allowed(self.client, reverse('acct-login'),
                     {'username': 'adam', 'password': 'abc'},
                     reverse('acct-my-profile'))

        # get authenticated pages
        get_allowed(self.client, reverse('acct-my-profile'),
                    ['profile/account.html', 'base_profile.html'])

    def test_auth_views(self):
        """Test private views while logged in"""
        # pylint: disable=bad-whitespace

        self.client.login(username='adam', password='abc')

        # get authenticated pages
        get_allowed(self.client,
            reverse('acct-my-profile'),
            ['profile/account.html', 'base_profile.html'])
        get_allowed(self.client,
            reverse('acct-update'),
            ['forms/account/update.html', 'forms/base_form.html'])
        get_allowed(self.client,
            reverse('acct-change-pw'),
            ['forms/account/pw_change.html', 'forms/base_form.html'])
        get_allowed(self.client,
            reverse('acct-buy-requests'),
            ['profile/account.html', 'base_profile.html'])

    def _test_post_view_helper(self, url, templates, data,
                               redirect_url='acct-my-profile', username='adam', password='abc'):
        """Helper for logging in, posting to a view, then checking the results"""
        # pylint: disable=too-many-arguments

        self.client.login(username=username, password=password)
        post_allowed_bad(self.client, reverse(url), templates)
        post_allowed(self.client, reverse(url), data,
                     reverse(redirect_url))

    def test_update_view(self):
        """Test the account update view"""
        # pylint: disable=bad-whitespace

        user = User.objects.get(username='adam')
        user_data = {'first_name': 'mitchell',        'last_name': 'kotler',
                     'email': 'mitch@muckrock.com',   'user': user,
                     'address1': '123 main st',       'address2': '',
                     'city': 'boston', 'state': 'MA', 'zip_code': '02140',
                     'phone': '555-123-4567',         'email_pref': 'instant'}

        self._test_post_view_helper(
            'acct-update',
            ['forms/account/update.html', 'forms/base_form.html'],
            user_data)

        user = User.objects.get(username='adam')
        profile = user.profile
        for key, val in user_data.iteritems():
            if key in ['first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(user, key))
            if key not in ['user', 'first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(profile, key))

    def test_change_pw_view(self):
        """Test the change pw view"""

        self._test_post_view_helper(
            'acct-change-pw',
            ['forms/account/pw_change.html', 'forms/base_form.html'],
            {'old_password': 'abc',
             'new_password1': '123',
             'new_password2': '123'},
            redirect_url='acct-change-pw-done')
        self.client.logout()
        nose.tools.assert_false(self.client.login(username='adam', password='abc'))
        nose.tools.assert_true(self.client.login(username='adam', password='123'))

    def test_manage_subsc_view(self):
        """Test managing your subscription"""

        # beta
        self.client.login(username='bob', password='abc')
        get_allowed(self.client, reverse('acct-manage-subsc'),
                    ['forms/account/subscription.html'])

        # admin
        self.client.login(username='admin', password='abc')
        get_allowed(self.client, reverse('acct-manage-subsc'),
                    ['profile/account.html', 'base_profile.html'])

        # update this for stripe for community and pro


    def test_buy_requests_view(self):
        """Test buying requests"""
        # write this

    def test_stripe_webhooks(self):
        """Test webhooks received from stripe"""
        kwargs = {"wsgi.url_scheme": "https"}

        response = self.client.post(reverse('acct-webhook'), {}, **kwargs)
        nose.tools.eq_(response.status_code, 404)

        response = self.client.post(reverse('acct-webhook'),
                                    {'json': json.dumps({'event': 'fake_event'})}, **kwargs)
        nose.tools.eq_(response.status_code, 404)

        response = self.client.post(reverse('acct-webhook'),
                                    {'json': json.dumps({'event': 'ping'})}, **kwargs)
        nose.tools.eq_(response.status_code, 200)
        webhook_json = open(os.path.join(
            SITE_ROOT,
            'accounts/fixtures/webhook_recurring_payment_failed.json'
        )).read()
        response = self.client.post(reverse('acct-webhook'), {'json': webhook_json}, **kwargs)
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_(len(mail.outbox), 1)
        nose.tools.eq_(mail.outbox[-1].to, ['adam@example.com'])
        webhook_json = open(os.path.join(
            SITE_ROOT,
            'accounts/fixtures/webhook_subscription_final_payment_attempt_failed.json'
        )).read()
        response = self.client.post(reverse('acct-webhook'), {'json': webhook_json}, **kwargs)
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_(len(mail.outbox), 2)
        nose.tools.eq_(mail.outbox[-1].to, ['adam@example.com'])

    def test_logout_view(self):
        """Test the logout view"""

        self.client.login(username='adam', password='abc')

        # logout & check
        get_allowed(self.client, reverse('acct-logout'),
                    ['front_page.html'])
        get_post_unallowed(self.client, reverse('acct-my-profile'))
