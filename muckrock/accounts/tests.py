"""
Tests using nose for the accounts application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import TestCase, RequestFactory

from datetime import datetime, date, timedelta
import json
import logging
from mock import Mock, patch
import nose.tools

from muckrock.accounts.forms import UserChangeForm, RegisterForm
from muckrock.accounts import views as accounts_views
from muckrock.factories import UserFactory, ProfileFactory
from muckrock.organization.models import Organization
from muckrock.settings import MONTHLY_REQUESTS
from muckrock.utils import get_stripe_token, mock_middleware

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises
logger = logging.getLogger(__name__)

# allow long names, methods that could be functions and too many public methods in tests
# pylint: disable=invalid-name
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=no-member

# Creates mock items for testing methods that involve Stripe
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

def http_get_response(url, view, user=AnonymousUser()):
    """Handles making GET requests, returns the response."""
    request_factory = RequestFactory()
    request = request_factory.get(url)
    request = mock_middleware(request)
    request.user = user
    response = view(request)
    return response

def http_post_response(url, view, data, user=AnonymousUser()):
    """Handles making POST requests, returns the response."""
    request_factory = RequestFactory()
    request = request_factory.post(url, data)
    request = mock_middleware(request)
    request.user = user
    response = view(request)
    return response


class TestBasicSignupView(TestCase):
    """The BasicSignupView handles registration of basic accounts."""
    def setUp(self):
        self.view = accounts_views.BasicSignupView.as_view()
        self.url = reverse('accounts-signup-basic')
        self.data = {
            'username': 'test-user',
            'email': 'test@muckrock.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'password',
            'password2': 'password'
        }

    def test_logged_out_get(self):
        """Getting the view while logged out should show the registration form."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 200)

    def test_logged_in_get(self):
        """Getting the view while logged in should redirect."""
        user = UserFactory()
        response = http_get_response(self.url, self.view, user)
        eq_(response.status_code, 302)

    def test_logged_out_post(self):
        """Posting valid data while logged out should create a new basic account."""
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 302,
            'Should redirect to the new account upon creation.')
        user = User.objects.get(username=self.data['username'])
        ok_(user, 'The user should be created.')
        eq_(user.profile.acct_type, 'basic', 'The user should be given a basic plan.')

    @raises(User.DoesNotExist)
    def test_logged_in_post(self):
        """Posting valid data while logged in should redirect without creating a new user."""
        user = UserFactory()
        response = http_post_response(self.url, self.view, self.data, user)
        eq_(response.status_code, 302)
        User.objects.get(username=self.data['username'])


class TestProfessionalSignupView(TestCase):
    """The ProfessionalSignupView handles registration and subscription of professional accounts."""
    def setUp(self):
        self.view = accounts_views.ProfessionalSignupView.as_view()
        self.url = reverse('accounts-signup-professional')
        self.data = {
            'username': 'test-user',
            'email': 'test@muckrock.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'password',
            'password2': 'password',
            'token': 'test'
        }

    def test_logged_out_get(self):
        """Getting the view while logged out should show the registration form."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 200)

    def test_logged_in_get(self):
        """Getting the view while logged in should redirect."""
        user = UserFactory()
        response = http_get_response(self.url, self.view, user)
        eq_(response.status_code, 302)

    @patch('muckrock.accounts.models.Profile.start_pro_subscription')
    def test_logged_out_post(self, mock_subscribe):
        """Posting valid data while logged out should create a new professional account."""
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 302,
            'Should redirect to the new account upon creation.')
        user = User.objects.get(username=self.data['username'])
        ok_(user, 'The user should be created.')
        ok_(mock_subscribe.called_once)

    @raises(User.DoesNotExist)
    def test_logged_in_post(self):
        """Posting valid data while logged in should redirect without creating a new user."""
        user = UserFactory()
        response = http_post_response(self.url, self.view, self.data, user)
        eq_(response.status_code, 302)
        User.objects.get(username=self.data['username'])


class TestAccountsView(TestCase):
    """The AccountsView handles the registration and modification of account plans."""
    def setUp(self):
        self.view = accounts_views.AccountsView.as_view()
        self.url = reverse('accounts')
        self.data = {
            'plan': '',
            'username': 'test-user',
            'email': 'test@muckrock.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'password',
            'password2': 'password'
        }

    def test_no_plan(self):
        """Posting registation data without a plan should return 400."""
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 400)

    def test_nonexistant_plan(self):
        """Posting registation data with a nonexistant plan should return 400."""
        self.data['plan'] = 'fartbutts'
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 400)

    def test_register_basic_account(self):
        """Posting the registration data with a basic plan should register the account."""
        self.data['plan'] = 'basic'
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 302,
            'Should redirect to the new account upon creation.')
        user = User.objects.get(username=self.data['username'])
        ok_(user, 'The user should be created.')
        eq_(user.profile.acct_type, 'basic', 'The user should be given a basic plan.')


    @patch('muckrock.accounts.models.Profile.start_pro_subscription')
    def test_register_pro_account(self, mock_subscribe):
        """
        Posting the registration data with a professional plan should
        register the account and start a pro subscription on their acccount.
        """
        self.data['plan'] = 'professional'
        self.data['token'] = 'test'
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 302,
            'Should redirect to the new account upon creation.')
        user = User.objects.get(username=self.data['username'])
        ok_(user, 'The user should be created.')
        ok_(mock_subscribe.called_once, 'The user should be subscribed to a pro account.')

    def test_register_org_account(self):
        """
        Posting the registation data with an organization plan should
        register the account and create the organization.
        """
        self.data['plan'] = 'organization'
        self.data['name'] = 'Test Org'
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 302,
            'Shoould redirect to the new org\'s activation page upon creation.')
        user = User.objects.get(username=self.data['username'])
        org = Organization.objects.get(name=self.data['name'])
        ok_(user, 'The user should be created.')
        ok_(org, 'The organization should be created.')
        eq_(org.owner, user, 'The user should be made the owner of the organization.')

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


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Charge', mock_charge)
class TestProfileUnit(TestCase):
    """Unit tests for profile model"""
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
        profile = ProfileFactory(num_requests=0)
        profile.date_update = datetime.now()
        nose.tools.assert_false(profile.make_request())

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
    """Tests stripe integration and error handling"""
    def setUp(self):
        self.profile = ProfileFactory()

    @nose.tools.nottest
    def test_pay(self):
        """Test making a payment"""
        token = get_stripe_token()
        metadata = {
            'email': self.profile.user.email,
            'action': 'test-charge'
        }
        self.profile.pay(token, 100, metadata)

    @nose.tools.nottest
    def test_customer(self):
        """Test accessing the profile's Stripe customer"""
        ok_(not self.profile.customer_id)
        self.profile.customer()
        ok_(self.profile.customer_id,
            'The customer id should be saved so the customer can be retrieved later.')

    @nose.tools.nottest
    def test_subscription(self):
        """Test starting a subscription"""
        customer = self.profile.customer()
        customer.sources.create(source=get_stripe_token())
        customer.save()
        self.profile.start_pro_subscription()
        self.profile.cancel_pro_subscription()


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Charge', Mock())
class TestAccountFunctional(TestCase):
    """Functional tests for account"""
    def setUp(self):
        """Set up tests"""
        self.request_factory = RequestFactory()
        self.profile = ProfileFactory()

    def test_public_views(self):
        """Test public views while not logged in"""
        response = http_get_response(reverse('acct-login'), login)
        eq_(response.status_code, 200, 'Login page should be publicly visible.')
        # account overview page
        response = http_get_response(reverse('accounts'), accounts_views.AccountsView.as_view())
        eq_(response.status_code, 200, 'Top level accounts page should be publicly visible.')
        # profile page
        request = self.request_factory.get(self.profile.get_absolute_url())
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = accounts_views.profile(request, self.profile.user.username)
        eq_(response.status_code, 200, 'User profiles should be publicly visible.')

    def test_unallowed_views(self):
        """Private URLs should redirect logged-out users to the log in page"""
        def test_get_post(url, view, data):
            """Performs both a GET and a POST on the same url and view."""
            get_response = http_get_response(url, view)
            post_response = http_post_response(url, view, data)
            return (get_response, post_response)
        # my profile
        get, post = test_get_post(reverse('acct-my-profile'), accounts_views.profile, {})
        eq_(get.status_code, 302, 'My profile link reponds with 302 to logged out user.')
        eq_(post.status_code, 302, 'POST to my profile link responds with 302.')
        # settings
        get, post = test_get_post(reverse('acct-settings'), accounts_views.settings, {})
        eq_(get.status_code, 302, 'GET /profile responds with 302 to logged out user.')
        eq_(post.status_code, 302, 'POST /settings reponds with 302 to logged out user.')
        # buy requests
        buy_requests_url = reverse('acct-buy-requests', args=['test'])
        get, post = test_get_post(buy_requests_url, accounts_views.buy_requests, {})
        eq_(get.status_code, 302,
            'GET /profile/*/buy_requests/ responds with 302 to logged out user.')
        eq_(post.status_code, 302,
            'POST /profile/*/buy_requests/ responds with 302 to logged out user.')

    def test_auth_views(self):
        """Test private views while logged in"""
        user = self.profile.user
        # my profile
        response = http_get_response(reverse('acct-my-profile'), accounts_views.profile, user)
        eq_(response.status_code, 200, 'Logged in user may view their own profile.')
        # settings
        response = http_get_response(reverse('acct-settings'), accounts_views.settings, user)
        eq_(response.status_code, 200)
        # buy requests
        buy_requests_url = reverse('acct-buy-requests', args=[user.username])
        response = http_get_response(buy_requests_url, accounts_views.buy_requests, user)
        eq_(response.status_code, 302, 'Buying requests should respond with a redirect')

    def test_settings_view(self):
        """Test the account settings view"""
        user = self.profile.user
        user_data = {
            # USER DATA
            'first_name': 'mitchell',
            'last_name': 'kotler',
            'email': 'mitch@muckrock.com',
            # PROFILE DATA
            'user': user,
            'address1': '123 main st',
            'address2': '',
            'city': 'boston',
            'state': 'MA',
            'zip_code': '02140',
            'phone': '555-123-4567',
            'email_pref': 'instant'
        }
        settings_url = reverse('acct-settings')
        http_post_response(settings_url, accounts_views.settings, user_data, user)
        self.profile.refresh_from_db()
        for key, val in user_data.iteritems():
            if key in ['first_name', 'last_name', 'email']:
                eq_(val, getattr(user, key))
            else:
                eq_(val, getattr(self.profile, key))


class TestStripeWebhook(TestCase):
    """The Stripe webhook listens for events in order to issue receipts."""
    def setUp(self):
        self.mock_event = {
            'id': 'test-event',
            'type': 'mock.type',
            'data': {
                'object': {
                    'id': 'test-charge'
                }
            }
        }
        self.request_factory = RequestFactory()
        self.url = reverse('acct-webhook-v2')
        self.data = json.dumps(self.mock_event)

    def test_post_request(self):
        """Only POST requests should be allowed."""
        get_request = self.request_factory.get(self.url)
        response = accounts_views.stripe_webhook(get_request)
        eq_(response.status_code, 405, 'Should respond to GET request with 405')
        post_request = self.request_factory.post(
            self.url,
            data=self.data,
            content_type='application/json'
        )
        response = accounts_views.stripe_webhook(post_request)
        eq_(response.status_code, 200, 'Should respond to POST request with 200')

    def test_bad_json(self):
        """POSTing bad JSON should return a 400 status code."""
        post_request = self.request_factory.post(
            self.url,
            data=u'Not JSON',
            content_type='application/json'
        )
        response = accounts_views.stripe_webhook(post_request)
        eq_(response.status_code, 400)

    def test_missing_data(self):
        """POSTing unexpected JSON should return a 400 status code."""
        bad_data = json.dumps({'hello': 'world'})
        post_request = self.request_factory.post(
            self.url,
            data=bad_data,
            content_type='application/json'
        )
        response = accounts_views.stripe_webhook(post_request)
        eq_(response.status_code, 400)

    @patch('muckrock.message.tasks.send_charge_receipt.delay')
    def test_charge_succeeded(self, mock_task):
        """When a charge succeeded event is received, send a charge receipt."""
        self.mock_event['type'] = 'charge.succeeded'
        post_request = self.request_factory.post(
            self.url,
            data=json.dumps(self.mock_event),
            content_type='application/json'
        )
        response = accounts_views.stripe_webhook(post_request)
        eq_(response.status_code, 200)
        mock_task.called_once()

    @patch('muckrock.message.tasks.send_invoice_receipt.delay')
    def test_invoice_succeeded(self, mock_task):
        """When an invoice payment succeeded event is received, send an invoice receipt."""
        self.mock_event['type'] = 'invoice.payment_succeeded'
        post_request = self.request_factory.post(
            self.url,
            data=json.dumps(self.mock_event),
            content_type='application/json')
        response = accounts_views.stripe_webhook(post_request)
        eq_(response.status_code, 200)
        mock_task.called_once()

    @patch('muckrock.message.tasks.failed_payment.delay')
    def test_invoice_failed(self, mock_task):
        """When an invoice payment failed event is received, send a notification."""
        self.mock_event['type'] = 'invoice.payment_failed'
        post_request = self.request_factory.post(
            self.url,
            data=json.dumps(self.mock_event),
            content_type='application/json'
        )
        response = accounts_views.stripe_webhook(post_request)
        eq_(response.status_code, 200)
        mock_task.called_once()
