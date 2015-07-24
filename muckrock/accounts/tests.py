"""
Tests using nose for the accounts application
"""

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import TestCase

import json
import nose.tools
import stripe
import os
from datetime import datetime, timedelta
from mock import Mock, patch

from muckrock.accounts.models import Profile
from muckrock.accounts.forms import UserChangeForm, RegisterForm
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed
from muckrock.settings import MONTHLY_REQUESTS, SITE_ROOT

# allow long names, methods that could be functions and too many public methods in tests
# pylint: disable=C0103
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=E1103

mock_customer = Mock()
mock_customer.id = 'cus_2jPQblsYu5doOE'
mock_customer.active_card.last4 = '1234'
mock_customer.active_card.type = 'Visa'
MockCustomer = Mock()
MockCustomer.create.return_value = mock_customer
MockCustomer.retrieve.return_value = mock_customer

class TestAccountFormsUnit(TestCase):
    """Unit tests for account forms"""
    fixtures = ['test_users.json', 'test_profiles.json']

    def setUp(self):
        """Set up tests"""
        self.profile = Profile.objects.get(pk=1)

    def test_user_change_form_email_normal(self):
        """Changing email normally should succeed"""
        # pylint: disable=attribute-defined-outside-init
        form = UserChangeForm(instance=self.profile)
        form.cleaned_data = {}
        form.cleaned_data['email'] = 'new@example.com'
        nose.tools.eq_(form.clean_email(), 'new@example.com')

    def test_user_change_form_email_same(self):
        """Keeping email the same should succeed"""
        form = UserChangeForm(instance=self.profile)
        form.cleaned_data = {}
        form.cleaned_data['email'] = 'adam@example.com'
        nose.tools.eq_(form.clean_email(), 'adam@example.com')

    def test_user_change_form_email_conflict(self):
        """Trying to use an already taken email should fail"""
        form = UserChangeForm(instance=self.profile)
        form.cleaned_data = {}
        form.cleaned_data['email'] = 'bob@example.com'
        nose.tools.assert_raises(ValidationError, form.clean_email) # conflicting email

    def test_user_creation_form(self):
        """Create a new user - name/email should be unique (case insensitive)"""

        data = {'username': 'ADAM', 'email': 'notadam@example.com', 'first_name': 'adam',
                'last_name': 'smith', 'password1': '123', 'password2': '123'}
        form = RegisterForm(data)
        nose.tools.assert_false(form.is_valid())

        data = {'username': 'not_adam', 'email': 'ADAM@EXAMPLE.COM', 'first_name': 'adam',
                'last_name': 'smith', 'password1': '123', 'password2': '123'}
        form = RegisterForm(data)
        nose.tools.assert_false(form.is_valid())


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Charge', Mock())
class TestProfileUnit(TestCase):
    """Unit tests for profile model"""
    fixtures = ['test_users.json', 'test_profiles.json', 'test_stripeccs.json']

    def test_unicode(self):
        """Test profile model's __unicode__ method"""
        profile = Profile.objects.get(pk=1)
        nose.tools.eq_(unicode(profile), "Adam's Profile")

    def test_get_monthly_requests(self):
        """Normal get number reuqests just returns the current value"""
        profile = Profile.objects.get(pk=1)
        profile.date_update = datetime.now()
        nose.tools.eq_(profile.get_monthly_requests(), 25)

    def test_get_monthly_requests_refresh(self):
        """Get number requests resets the number of requests if its been over a month"""
        profile = Profile.objects.get(pk=2)
        profile.date_update = datetime.now() - timedelta(32)
        nose.tools.eq_(profile.get_monthly_requests(), MONTHLY_REQUESTS[profile.acct_type])
        nose.tools.ok_(datetime.now() - profile.date_update < timedelta(minutes=5))

    def test_make_request_refresh(self):
        """Make request resets count if it has been more than a month"""
        profile = Profile.objects.get(pk=3)
        profile.date_update = datetime.now() - timedelta(32)
        nose.tools.assert_true(profile.make_request())

    def test_make_request_pass_monthly(self):
        """Make request call decrements number of monthly requests"""
        profile = Profile.objects.get(pk=1)
        profile.date_update = datetime.now()
        profile.make_request()
        nose.tools.eq_(profile.monthly_requests, 24)

    def test_make_request_pass(self):
        """Make request call decrements number of requests if out of monthly requests"""
        profile = Profile.objects.get(pk=2)
        profile.date_update = datetime.now()
        profile.make_request()
        nose.tools.eq_(profile.num_requests, 9)

    def test_make_request_fail(self):
        """If out of requests, make request returns false"""
        profile = Profile.objects.get(pk=3)
        profile.date_update = datetime.now()
        nose.tools.assert_false(profile.make_request())

    def test_customer(self):
        """Test customer"""

        # customer exists
        profile = Profile.objects.get(pk=1)
        customer = profile.customer()
        nose.tools.eq_(customer, mock_customer)

        # customer doesn't exist
        with patch('stripe.Customer') as NewMockCustomer:
            new_mock_customer = Mock()
            new_mock_customer.id = 'cus_PKt7LZD6fbFdpC'
            NewMockCustomer.retrieve.side_effect = stripe.InvalidRequestError('Message', 'Param')
            NewMockCustomer.create.return_value = new_mock_customer

            profile = Profile.objects.get(pk=1)
            customer = profile.customer()
            nose.tools.eq_(customer, new_mock_customer)

    def test_pay(self):
        """Test pay"""
        # rewrite this for stripe

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
        self.client.login(username='adam', password='abc')
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
