"""
Tests using nose for the accounts application
"""

from __future__ import absolute_import

from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import TestCase

import json
import nose.tools
import stripe
from datetime import datetime, timedelta
from mock import Mock, patch

from accounts.models import Profile
from accounts.forms import UserChangeForm, CreditCardForm, RegisterFree, \
                           PaymentForm, UpgradeSubscForm
from tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed
from settings import MONTHLY_REQUESTS

# allow long names, methods that could be functions and too many public methods in tests
# pylint: disable=C0103
# pylint: disable=R0201
# pylint: disable=R0904

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
        # pylint: disable=W0201
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

    def test_credit_card_form(self):
        """Test validation on credit card form"""
        data = {'token': 'token'}
        form = CreditCardForm(data)
        nose.tools.ok_(form.is_valid())

        data = {'foo': 'bar'}
        form = CreditCardForm(data)
        nose.tools.assert_false(form.is_valid())

    def test_upgrade_subsc_form_init(self):
        """Test UpgradeSubscForm's init"""
        mock_profile = Mock()
        mock_profile.get_cc.return_value = None
        mock_request = Mock()
        mock_request.user.get_profile.return_value = mock_profile
        form = UpgradeSubscForm(request=mock_request)
        nose.tools.ok_('use_on_file' not in form.fields)

        mock_card = Mock()
        mock_card.type = 'Visa'
        mock_card.last4 = '1234'
        mock_profile.get_cc.return_value = mock_card
        form = UpgradeSubscForm(request=mock_request)
        nose.tools.eq_(form.fields['use_on_file'].help_text, 'Visa ending in 1234')

    def test_upgrade_subsc_form_clean(self):
        """Test UpgradeSubscForm's clean"""
        mock_card = Mock()
        mock_card.type = 'Visa'
        mock_card.last4 = '1234'
        mock_profile = Mock()
        mock_profile.get_cc.return_value = mock_card
        mock_request = Mock()
        mock_request.user.get_profile.return_value = mock_profile

        data = {'token': 'token', 'use_on_file': False}
        form = UpgradeSubscForm(data, request=mock_request)
        nose.tools.ok_(form.is_valid())

        data = {'use_on_file': False}
        form = UpgradeSubscForm(data, request=mock_request)
        nose.tools.assert_false(form.is_valid())

        data = {'use_on_file': True}
        form = UpgradeSubscForm(data, request=mock_request)
        nose.tools.ok_(form.is_valid())

    def test_payment_form_clean(self):
        """Test PaymentForm's clean"""
        mock_request = Mock()
        data = {'use_on_file': True, 'save_cc': True}
        form = PaymentForm(data, request=mock_request)
        nose.tools.assert_false(form.is_valid())

        data = {'token': 'token', 'use_on_file': False, 'save_cc': True}
        form = PaymentForm(data, request=mock_request)
        nose.tools.ok_(form.is_valid())

    def test_user_creation_form(self):
        """Create a new user - name/email should be unique (case insensitive)"""

        data = {'username': 'ADAM', 'email': 'notadam@example.com', 'first_name': 'adam',
                'last_name': 'smith', 'password1': '123', 'password2': '123'}
        form = RegisterFree(data)
        nose.tools.assert_false(form.is_valid())

        data = {'username': 'not_adam', 'email': 'ADAM@EXAMPLE.COM', 'first_name': 'adam',
                'last_name': 'smith', 'password1': '123', 'password2': '123'}
        form = RegisterFree(data)
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

    def test_get_cc(self):
        """Test get_cc"""

        profile = Profile.objects.get(pk=1)
        card = profile.get_cc()
        nose.tools.eq_(card.last4, mock_customer.active_card.last4)
        nose.tools.eq_(card.type,  mock_customer.active_card.type)

        with patch('stripe.Customer') as NewMockCustomer:
            new_mock_customer = Mock()
            new_mock_customer.active_card = None
            NewMockCustomer.retrieve.return_value = new_mock_customer

            profile = Profile.objects.get(pk=1)
            card = profile.get_cc()
            nose.tools.ok_(card is None)

    def test_get_customer(self):
        """Test get_customer"""

        # customer exists
        profile = Profile.objects.get(pk=1)
        customer = profile.get_customer()
        nose.tools.eq_(customer, mock_customer)

        # customer doesn't exist
        with patch('stripe.Customer') as NewMockCustomer:
            new_mock_customer = Mock()
            new_mock_customer.id = 'cus_PKt7LZD6fbFdpC'
            NewMockCustomer.retrieve.side_effect = stripe.InvalidRequestError('Message', 'Param')
            NewMockCustomer.create.return_value = new_mock_customer

            profile = Profile.objects.get(pk=1)
            customer = profile.get_customer()
            nose.tools.eq_(customer, new_mock_customer)

    def test_save_customer(self):
        """Test save_cc"""
        profile = Profile.objects.get(pk=1)
        customer = profile.save_customer('token')
        nose.tools.eq_(customer, mock_customer)
        nose.tools.eq_(profile.stripe_id, mock_customer.id)
        nose.tools.eq_(stripe.Customer.create.call_args, ((),
                       {'description': profile.user.username,
                        'email': profile.user.email,
                        'card': 'token',
                        'plan': 'pro'}))

    def test_pay(self):
        """Test pay"""
        profile = Profile.objects.get(pk=1)
        form = Mock()

        # save cc = true
        form.cleaned_data = {'save_cc': True, 'token': 'token'}
        profile.pay(form, 4200, 'description')
        nose.tools.eq_(stripe.Charge.create.call_args, ((),
                       {'amount': 4200,
                        'currency': 'usd',
                        'customer': profile.get_customer().id,
                        'description': 'description'}))

        # save cc = false and use on file = false, has a token
        form.cleaned_data = {'use_on_file': False, 'save_cc': False, 'token': 'token'}
        profile.pay(form, 4200, 'description')
        nose.tools.eq_(stripe.Charge.create.call_args, ((),
                       {'amount': 4200,
                        'currency': 'usd',
                        'card': 'token',
                        'description': 'description'}))


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

        urls_and_templates = [
                (reverse('acct-profile', args=['adam']), 'registration/profile.html'),
                (reverse('acct-login'),                  'registration/login.html'),
                (reverse('acct-register'),               'registration/register.html'),
                (reverse('acct-register-free'),          'registration/register_free.html'),
                (reverse('acct-register-pro'),           'registration/cc.html'),
                (reverse('acct-reset-pw'),               'registration/password_reset_form.html'),
                (reverse('acct-logout'),                 'registration/logged_out.html'),
                ]

        for url, template in urls_and_templates:
            get_allowed(self.client, url, [template, 'registration/base.html'])

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        # get/post authenticated pages while unauthenticated
        url_names = ['acct-my-profile', 'acct-update', 'acct-change-pw', 'acct-update-cc',
                     'acct-manage-subsc', 'acct-buy-requests']
        for url_name in url_names:
            get_post_unallowed(self.client, reverse(url_name))

        # post unathenticated pages
        post_allowed_bad(self.client, reverse('acct-register-free'),
                         ['registration/register_free.html', 'registration/base.html'])

    def test_register_free_view(self):
        """Test the register-free view"""

        post_allowed_bad(self.client, reverse('acct-register-free'),
                         ['registration/register_free.html', 'registration/base.html'])
        post_allowed(self.client, reverse('acct-register-free'),
                     {'username': 'test1', 'password1': 'abc', 'password2': 'abc',
                      'email': 'test@example.com', 'first_name': 'first', 'last_name': 'last'},
                     reverse('acct-my-profile'))

        # get authenticated pages
        get_allowed(self.client, reverse('acct-my-profile'),
                    ['registration/profile.html', 'registration/base.html'])

    def test_register_pro_view(self):
        """Test the register-pro view"""
        post_allowed_bad(self.client, reverse('acct-register-pro'),
                         ['registration/cc.html', 'registration/base.html'])
        post_allowed(self.client, reverse('acct-register-pro'),
                     {'username': 'test1', 'password1': 'abc', 'password2': 'abc',
                      'email': 'test@example.com', 'first_name': 'first', 'last_name': 'last',
                      'token': 'token'},
                     reverse('acct-my-profile'))

        # get authenticated pages
        get_allowed(self.client, reverse('acct-my-profile'),
                    ['registration/profile.html', 'registration/base.html'])

    def test_login_view(self):
        """Test the login view"""

        # bad user name
        post_allowed_bad(self.client, reverse('acct-login'),
                         ['registration/login.html', 'registration/base.html'],
                         data={'username': 'nouser', 'password': 'abc'})
        # bad pw
        post_allowed_bad(self.client, reverse('acct-login'),
                         ['registration/login.html', 'registration/base.html'],
                         data={'username': 'adam', 'password': 'bad pw'})
        # succesful login
        post_allowed(self.client, reverse('acct-login'),
                     {'username': 'adam', 'password': 'abc'},
                     reverse('acct-my-profile'))

        # get authenticated pages
        get_allowed(self.client, reverse('acct-my-profile'),
                    ['registration/profile.html', 'registration/base.html'])

    def test_auth_views(self):
        """Test private views while logged in"""

        self.client.login(username='adam', password='abc')

        # get authenticated pages
        urls_and_templates = [
                ('acct-my-profile',   'registration/profile.html'),
                ('acct-update',       'registration/update.html'),
                ('acct-change-pw',    'registration/password_change_form.html'),
                ('acct-update-cc',    'registration/cc.html'),
                ('acct-buy-requests', 'registration/cc.html'),
                ]

        for url_name, template in urls_and_templates:
            get_allowed(self.client, reverse(url_name), [template, 'registration/base.html'])

    def _test_post_view_helper(self, url, template, data,
                               redirect_url='acct-my-profile', username='adam', password='abc'):
        """Helper for logging in, posting to a view, then checking the results"""
        # pylint: disable=R0913

        self.client.login(username=username, password=password)
        post_allowed_bad(self.client, reverse(url),
                         ['registration/%s.html' % template, 'registration/base.html'])
        post_allowed(self.client, reverse(url), data,
                     reverse(redirect_url))

    def test_update_view(self):
        """Test the account update view"""

        user = User.objects.get(username='adam')
        user_data = {'first_name': 'mitchell',        'last_name': 'kotler',
                     'email': 'mitch@muckrock.com',   'user': user,
                     'address1': '123 main st',       'address2': '',
                     'city': 'boston', 'state': 'MA', 'zip_code': '02140',
                     'phone': '555-123-4567'}

        self._test_post_view_helper('acct-update', 'update', user_data)

        user = User.objects.get(username='adam')
        profile = user.get_profile()
        for key, val in user_data.iteritems():
            if key in ['first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(user, key))
            if key not in ['user', 'first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(profile, key))

    def test_change_pw_view(self):
        """Test the change pw view"""

        self._test_post_view_helper('acct-change-pw', 'password_change_form',
                                    {'old_password': 'abc',
                                     'new_password1': '123',
                                     'new_password2': '123'},
                                    redirect_url='acct-change-pw-done')
        self.client.logout()
        nose.tools.assert_false(self.client.login(username='adam', password='abc'))
        nose.tools.assert_true (self.client.login(username='adam', password='123'))

    def test_update_cc_view(self):
        """Test updating a credit card"""

        self._test_post_view_helper('acct-update-cc', 'cc',
                                    {'token': 'token-update-cc'})
        nose.tools.eq_(mock_customer.card, 'token-update-cc')
        mock_customer.save.assert_called_once_with()

        with patch('stripe.Customer') as NewMockCustomer:
            new_mock_customer = Mock()
            new_mock_customer.active_card = None
            NewMockCustomer.retrieve.return_value = new_mock_customer
            self._test_post_view_helper('acct-update-cc', 'cc',
                                        {'token': 'token-update-cc'})
            nose.tools.eq_(mock_customer.card, 'token-update-cc')
            mock_customer.save.assert_called_once_with()

    def test_manage_subsc_view(self):
        """Test managing your subscription"""

        # beta
        self.client.login(username='adam', password='abc')
        get_allowed(self.client, reverse('acct-manage-subsc'),
                    ['registration/subsc.html', 'registration/base.html'],
                    context={'heading': 'Beta Account'})

        # admin
        self.client.login(username='admin', password='abc')
        get_allowed(self.client, reverse('acct-manage-subsc'),
                    ['registration/subsc.html', 'registration/base.html'],
                    context={'heading': 'Admin Account'})

        # community with card on file
        self.client.login(username='community', password='abc')
        get_allowed(self.client, reverse('acct-manage-subsc'),
                    ['registration/cc.html', 'registration/base.html'],
                    context={'heading': 'Upgrade to a Pro Account'})
        post_allowed_bad(self.client, reverse('acct-manage-subsc'),
                         ['registration/cc.html', 'registration/base.html'])
        post_allowed(self.client, reverse('acct-manage-subsc'),
                     {'use_on_file': True},
                     reverse('acct-my-profile'))
        comm_user_profile = User.objects.get(username='community').get_profile()
        nose.tools.eq_(comm_user_profile.acct_type, 'pro')
        mock_customer.update_subscription.assert_called_once_with(plan='pro')

        # community with new card
        comm_user_profile.acct_type = 'community'
        comm_user_profile.save()
        post_allowed(self.client, reverse('acct-manage-subsc'),
                     {'token': 'token'},
                     reverse('acct-my-profile'))
        comm_user_profile = User.objects.get(username='community').get_profile()
        nose.tools.eq_(comm_user_profile.acct_type, 'pro')
        mock_customer.save.assert_called_once_with()

        # pro
        self.client.login(username='pro', password='abc')
        get_allowed(self.client, reverse('acct-manage-subsc'),
                    ['registration/subsc.html', 'registration/base.html'],
                    context={'heading': 'Cancel Your Subscription'})
        post_allowed(self.client, reverse('acct-manage-subsc'),
                     {'confirm': True},
                     reverse('acct-my-profile'))
        nose.tools.eq_(Profile.objects.get(user__username='pro').acct_type, 'community')
        mock_customer.cancel_subscription.assert_called_once_with()

    def test_buy_requests_view(self):
        """Test buying requests"""

        self._test_post_view_helper('acct-buy-requests', 'cc',
                                    {'token': 'token', 'save_cc': True})
        profile = Profile.objects.get(user__username='adam')
        nose.tools.eq_(profile.num_requests, 15)
        nose.tools.eq_(stripe.Charge.create.call_args, ((),
                       {'amount': 2000,
                        'currency': 'usd',
                        'customer': profile.get_customer().id,
                        'description': 'Charge for 5 requests'}))

        with patch('stripe.Charge') as NewMockCharge:
            NewMockCharge.create.side_effect = stripe.CardError('Message', 'Param', 'Code')
            post_allowed(self.client, reverse('acct-buy-requests'),
                         {'token': 'token', 'save_cc': True},
                         reverse('acct-buy-requests'))
            profile = Profile.objects.get(user__username='adam')
            nose.tools.eq_(profile.num_requests, 15)

    def test_stripe_webhooks(self):
        """Test webhooks received from stripe"""

        response = self.client.post(reverse('acct-webhook'), {})
        nose.tools.eq_(response.status_code, 404)

        response = self.client.post(reverse('acct-webhook'),
                                    {'json': json.dumps({'event': 'fake_event'})})
        nose.tools.eq_(response.status_code, 404)

        response = self.client.post(reverse('acct-webhook'),
                                    {'json': json.dumps({'event': 'ping'})})
        nose.tools.eq_(response.status_code, 200)

        webhook_json = open('accounts/fixtures/webhook_recurring_payment_failed.json').read()
        response = self.client.post(reverse('acct-webhook'), {'json': webhook_json})
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_(len(mail.outbox), 1)
        nose.tools.eq_(mail.outbox[-1].to, ['adam@example.com'])

        webhook_json = open('accounts/fixtures/'
                            'webhook_subscription_final_payment_attempt_failed.json').read()
        response = self.client.post(reverse('acct-webhook'), {'json': webhook_json})
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_(len(mail.outbox), 2)
        nose.tools.eq_(mail.outbox[-1].to, ['adam@example.com'])

    def test_logout_view(self):
        """Test the logout view"""

        self.client.login(username='adam', password='abc')

        # logout & check
        get_allowed(self.client, reverse('acct-logout'),
                    ['registration/logged_out.html', 'registration/base.html'])
        get_post_unallowed(self.client, reverse('acct-my-profile'))

    def test_admin_views(self):
        """Test additional admin views"""

        self.client.login(username='adam', password='abc')
        response = get_allowed(self.client, reverse('admin:stats-csv'))
        nose.tools.eq_(response['content-type'], 'text/csv')

