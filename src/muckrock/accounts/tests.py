"""
Tests using nose for the accounts application
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import TestCase

import nose.tools
import stripe
from datetime import datetime, timedelta
from mock import Mock, patch

from accounts.models import Profile, StripeCC
from accounts.forms import UserChangeForm, CreditCardForm, RegisterFree, \
                           PaymentForm, UpgradeSubscForm
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed
from settings import MONTHLY_REQUESTS

# allow long names, methods that could be functions and too many public methods in tests
# pylint: disable-msg=C0103
# pylint: disable-msg=R0201
# pylint: disable-msg=R0904

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
        # pylint: disable-msg=W0201
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
        data = {'token': 'token', 'last4': '1234', 'card_type': 'Visa'}
        form = CreditCardForm(data)
        nose.tools.ok_(form.is_valid())

        for data in [{'last4': '1234', 'card_type': 'Visa'},
                     {'token': 'token', 'card_type': 'Visa'},
                     {'token': 'token', 'last4': '1234'}]:
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
        mock_card.card_type = 'Visa'
        mock_card.last4 = '1234'
        mock_profile.get_cc.return_value = mock_card
        form = UpgradeSubscForm(request=mock_request)
        nose.tools.eq_(form.fields['use_on_file'].help_text, 'Visa ending in 1234')

    def test_upgrade_subsc_form_clean(self):
        """Test UpgradeSubscForm's clean"""
        mock_card = Mock()
        mock_card.card_type = 'Visa'
        mock_card.last4 = '1234'
        mock_profile = Mock()
        mock_profile.get_cc.return_value = mock_card
        mock_request = Mock()
        mock_request.user.get_profile.return_value = mock_profile

        data = {'token': 'token', 'last4': '1234', 'card_type': 'Visa', 'use_on_file': False}
        form = UpgradeSubscForm(data, request=mock_request)
        nose.tools.ok_(form.is_valid())

        data = {'last4': '1234', 'card_type': 'Visa', 'use_on_file': False}
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

        data = {'token': 'token', 'last4': '1234', 'card_type': 'Visa',
                'use_on_file': False, 'save_cc': True}
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

        def helper(profile_id, expected_card):
            """Helper to test get_cc"""
            profile = Profile.objects.get(pk=profile_id)
            card = profile.get_cc()
            if expected_card:
                nose.tools.eq_(card.last4, expected_card.last4)
                nose.tools.eq_(card.card_type, expected_card.type)
                nose.tools.eq_(card.user, profile.user)
            else:
                nose.tools.ok_(card is None)

        # no local, remote
        helper(1, mock_customer.active_card)
        # local and remote different - remote wins
        helper(2, mock_customer.active_card)

        with patch('stripe.Customer') as NewMockCustomer:
            new_mock_customer = Mock()
            new_mock_customer.active_card = None
            NewMockCustomer.retrieve.return_value = new_mock_customer

            # no local and no remote
            helper(1, None)
            # local and no remote different - delete local
            helper(2, None)

    def test_save_cc(self):
        """Test save_cc"""

        for profile_id in xrange(1, 3):
            # test once with and without a stripecc on file
            profile = Profile.objects.get(pk=profile_id)
            form = Mock()
            form.cleaned_data = {'token': 'token', 'last4': '5678', 'card_type': 'MasterCard'}
            profile.save_cc(form)
            card = StripeCC.objects.get(user=profile.user)
            nose.tools.eq_(card.last4, '5678')
            nose.tools.eq_(card.card_type, 'MasterCard')
            nose.tools.eq_(card.user, profile.user)

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
        form.cleaned_data = {'save_cc': True, 'token': 'token',
                             'last4': '5678', 'card_type': 'MasterCard'}
        profile.pay(Mock(), form, 4200, 'description')
        nose.tools.eq_(stripe.Charge.create.call_args, ((),
                       {'amount': 4200,
                        'currency': 'usd',
                        'customer': profile.get_customer().id,
                        'description': 'description'}))
        card = StripeCC.objects.get(user=profile.user)
        nose.tools.eq_(card.last4, '5678')

        # save cc = false and use on file = false, has a token
        form.cleaned_data = {'use_on_file': False, 'save_cc': False, 'token': 'token'}
        profile.pay(Mock(), form, 4200, 'description')
        nose.tools.eq_(stripe.Charge.create.call_args, ((),
                       {'amount': 4200,
                        'currency': 'usd',
                        'card': 'token',
                        'description': 'description'}))

        # save cc = false and use on file = true, exception
        with patch('stripe.Charge') as NewMockCharge:
            NewMockCharge.create.side_effect = stripe.CardError('Message', 'Param', 'Code')
            mock_request = Mock()

            form.cleaned_data = {'use_on_file': True, 'save_cc': False}
            profile.pay(mock_request, form, 4200, 'description')


class TestStripeCCUnit(TestCase):
    """Unit tests for strip cc model"""
    fixtures = ['test_users.json', 'test_profiles.json', 'test_stripeccs.json']

    def test_unicode(self):
        """Test stripe cc model's __unicode__ method"""
        stripecc = StripeCC.objects.get(pk=1)
        nose.tools.eq_(unicode(stripecc), "Bob's Visa ending in 1357")


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Charge', Mock())
class TestAccountFunctional(TestCase):
    """Functional tests for account"""
    fixtures = ['test_users.json', 'test_profiles.json', 'test_statistics.json']

    # views
    def test_anon_views(self):
        """Test public views while not logged in"""

        urls_and_templates = [
                (reverse('acct-profile', args=['adam']), 'registration/profile.html'),
                (reverse('acct-login'),                  'registration/login.html'),
                (reverse('acct-register'),               'registration/register.html'),
                (reverse('acct-reset-pw'),               'registration/password_reset_form.html'),
                (reverse('acct-logout'),                 'registration/logged_out.html'),
                ]

        for url, template in urls_and_templates:
            get_allowed(self.client, url, [template, 'registration/base.html'])

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        # get/post authenticated pages while unauthenticated
        url_names = ['acct-my-profile', 'acct-update', 'acct-change-pw']
        for url_name in url_names:
            get_post_unallowed(self.client, reverse(url_name))

        # post unathenticated pages
        post_allowed_bad(self.client, reverse('acct-register'),
                         ['registration/register.html', 'registration/base.html'])

    def test_register_view(self):
        """Test the register view"""

        post_allowed_bad(self.client, reverse('acct-register-free'),
                         ['registration/register_free.html', 'registration/base.html'])
        post_allowed(self.client, reverse('acct-register-free'),
                     {'username': 'test1', 'password1': 'abc', 'password2': 'abc',
                      'email': 'test@example.com', 'first_name': 'first', 'last_name': 'last'},
                     'http://testserver' + reverse('acct-my-profile'))

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
                     'http://testserver' + reverse('acct-my-profile'))

        # get authenticated pages
        get_allowed(self.client, reverse('acct-my-profile'),
                    ['registration/profile.html', 'registration/base.html'])

    def test_auth_views(self):
        """Test private views while logged in"""

        self.client.login(username='adam', password='abc')

        # get authenticated pages
        urls_and_templates = [
                ('acct-my-profile', 'registration/profile.html'),
                ('acct-update',     'registration/update.html'),
                ('acct-change-pw',  'registration/password_change_form.html'),
                ]

        for url_name, template in urls_and_templates:
            get_allowed(self.client, reverse(url_name), [template, 'registration/base.html'])

        # post authenticated pages
        post_allowed_bad(self.client, reverse('acct-update'),
                         ['registration/update.html', 'registration/base.html'])
        post_allowed_bad(self.client, reverse('acct-change-pw'),
                         ['registration/password_change_form.html', 'registration/base.html'])

    def test_post_views(self):
        """Test posting data in views while logged in"""

        self.client.login(username='adam', password='abc')
        user = User.objects.get(username='adam')

        user_data = {'first_name': 'mitchell',        'last_name': 'kotler',
                     'email': 'mitch@muckrock.com',   'user': user,
                     'address1': '123 main st',       'address2': '',
                     'city': 'boston', 'state': 'MA', 'zip_code': '02140',
                     'phone': '555-123-4567'}
        post_allowed(self.client, reverse('acct-update'), user_data,
            'http://testserver' + reverse('acct-my-profile'))

        user = User.objects.get(username='adam')
        profile = user.get_profile()
        for key, val in user_data.iteritems():
            if key in ['first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(user, key))
            if key not in ['user', 'first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(profile, key))

        post_allowed(self.client, reverse('acct-change-pw'),
                    {'old_password': 'abc',
                     'new_password1': '123',
                     'new_password2': '123'},
                     'http://testserver' + reverse('acct-change-pw-done'))

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

