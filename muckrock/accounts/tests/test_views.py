"""
Tests accounts views
"""

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase, RequestFactory

from mock import Mock, patch
from nose.tools import eq_, ok_, raises

from muckrock.accounts import views
from muckrock.factories import UserFactory, OrganizationFactory
from muckrock.organization.models import Organization
from muckrock.utils import mock_middleware

# pylint:disable=no-member

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

def http_get_post(url, view, data):
    """Performs both a GET and a POST on the same url and view."""
    get_response = http_get_response(url, view)
    post_response = http_post_response(url, view, data)
    return (get_response, post_response)

class TestBasicSignupView(TestCase):
    """The BasicSignupView handles registration of basic accounts."""
    def setUp(self):
        self.view = views.BasicSignupView.as_view()
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
        self.view = views.ProfessionalSignupView.as_view()
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


class TestOrganizationSignupView(TestCase):
    """The OrganizationSignupView handles registration of organization accounts."""
    def setUp(self):
        self.view = views.OrganizationSignupView.as_view()
        self.url = reverse('accounts-signup-organization')
        self.data = {
            'username': 'test-user',
            'email': 'test@muckrock.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'password',
            'password2': 'password',
            'organization_name': 'Test Org'
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
        """Posting valid data while logged out should create a new professional account."""
        response = http_post_response(self.url, self.view, self.data)
        eq_(response.status_code, 302,
            'Should redirect to the org activation page upon creation.')
        user = User.objects.get(username=self.data['username'])
        org = Organization.objects.get(name=self.data['organization_name'])
        ok_(user, 'The user should be created.')
        ok_(org, 'The org should be created.')
        eq_(org.owner, user, 'The user should be made an owner of the org.')

    @raises(User.DoesNotExist)
    def test_logged_in_post(self):
        """Posting valid data while logged in should redirect without creating a new user."""
        user = UserFactory()
        response = http_post_response(self.url, self.view, self.data, user)
        eq_(response.status_code, 302)
        User.objects.get(username=self.data['username'])


class TestAccountsView(TestCase):
    """The AccountsView allows users to choose an account plan that is right for them."""
    def setUp(self):
        self.user = UserFactory()
        self.view = views.AccountsView.as_view()
        self.url = reverse('accounts')

    def test_get(self):
        """Getting the view should show the available plans."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 200, 'Should be visible to anyone')

    @patch('muckrock.accounts.models.Profile.start_pro_subscription')
    def test_upgrade(self, mock_subscribe):
        """Logged in users should be able to upgrade to Pro accounts."""
        data = {
            'action': 'upgrade',
            'stripe_token': 'test'
        }
        response = http_post_response(self.url, self.view, data, self.user)
        eq_(response.status_code, 200)
        mock_subscribe.assert_called_once_with(data['stripe_token'])

    @patch('muckrock.accounts.models.Profile.start_pro_subscription')
    def test_upgrade_logged_out(self, mock_subscribe):
        """Logged out users should not be able to upgrade."""
        data = {
            'action': 'upgrade',
            'stripe_token': 'test'
        }
        response = http_post_response(self.url, self.view, data)
        eq_(response.status_code, 200)
        ok_(not mock_subscribe.called)

    @patch('muckrock.accounts.models.Profile.cancel_pro_subscription')
    def test_downgrade(self, mock_unsubscribe):
        """Logged in pro users should be able to downgrade to a Basic account."""
        data = {'action': 'downgrade'}
        pro_user = UserFactory(profile__acct_type='pro')
        response = http_post_response(self.url, self.view, data, pro_user)
        eq_(response.status_code, 200)
        ok_(mock_unsubscribe.called)

    @patch('muckrock.accounts.models.Profile.cancel_pro_subscription')
    def test_downgrade_not_pro(self, mock_unsubscribe):
        """A user who is not a pro cannot downgrade."""
        data = {'action': 'downgrade'}
        response = http_post_response(self.url, self.view, data, self.user)
        eq_(response.status_code, 200)
        ok_(not mock_unsubscribe.called)

    @patch('muckrock.accounts.models.Profile.cancel_pro_subscription')
    def test_downgrade_logged_out(self, mock_unsubscribe):
        """Logged out users cannot downgrade."""
        data = {'action': 'downgrade'}
        response = http_post_response(self.url, self.view, data)
        eq_(response.status_code, 200)
        ok_(not mock_unsubscribe.called)


@patch('stripe.Charge', Mock())
class TestBuyRequestsView(TestCase):
    """The buy requests view allows one user to buy requests for another, including themselves."""
    def setUp(self):
        self.user = UserFactory()
        self.factory = RequestFactory()
        self.url = reverse('acct-buy-requests', kwargs={'username': self.user.username})
        self.view = views.buy_requests
        self.data = {
            'stripe_token': 'test',
            'stripe_email': self.user.email
        }

    def test_buy_requests(self):
        """A user should be able to buy themselves requests."""
        existing_request_count = self.user.profile.num_requests
        post_request = self.factory.post(self.url, self.data)
        post_request = mock_middleware(post_request)
        post_request.user = self.user
        self.view(post_request, self.user.username)
        self.user.profile.refresh_from_db()
        requests_to_add = settings.BUNDLED_REQUESTS[self.user.profile.acct_type]
        eq_(self.user.profile.num_requests, existing_request_count + requests_to_add)

    def test_buy_requests_as_pro(self):
        """A pro user should get an extra request in each bundle."""
        existing_request_count = self.user.profile.num_requests
        self.user.profile.acct_type = 'pro'
        self.user.profile.save()
        post_request = self.factory.post(self.url, self.data)
        post_request = mock_middleware(post_request)
        post_request.user = self.user
        self.view(post_request, self.user.username)
        self.user.profile.refresh_from_db()
        requests_to_add = settings.BUNDLED_REQUESTS[self.user.profile.acct_type]
        eq_(self.user.profile.num_requests, existing_request_count + requests_to_add)

    def test_buy_requests_as_org(self):
        """An org member should get an extra request in each bundle."""
        existing_request_count = self.user.profile.num_requests
        self.user.profile.organization = OrganizationFactory(active=True)
        self.user.profile.save()
        post_request = self.factory.post(self.url, self.data)
        post_request = mock_middleware(post_request)
        post_request.user = self.user
        self.view(post_request, self.user.username)
        self.user.profile.refresh_from_db()
        requests_to_add = 5
        eq_(self.user.profile.num_requests, existing_request_count + requests_to_add)

    @patch('muckrock.message.tasks.gift.delay')
    def test_buy_requests_for_another(self, mock_notify):
        """A user should be able to buy someone else requests."""
        other_user = UserFactory()
        existing_request_count = other_user.profile.num_requests
        post_request = self.factory.post(self.url, self.data)
        post_request = mock_middleware(post_request)
        # here is the cool part: the request user is the buyer and the URL user is the recipient
        post_request.user = self.user
        self.view(post_request, other_user.username)
        other_user.profile.refresh_from_db()
        requests_to_add = settings.BUNDLED_REQUESTS[self.user.profile.acct_type]
        eq_(other_user.profile.num_requests, existing_request_count + requests_to_add)
        ok_(mock_notify.called, 'The recipient should be notified of their gift by email.')

    def test_gift_requests_anonymously(self):
        """Logged out users should also be able to buy someone else requests."""
        other_user = UserFactory()
        existing_request_count = other_user.profile.num_requests
        post_request = self.factory.post(self.url, self.data)
        post_request = mock_middleware(post_request)
        post_request.user = AnonymousUser()
        self.view(post_request, other_user.username)
        other_user.profile.refresh_from_db()
        requests_to_add = 4
        eq_(other_user.profile.num_requests, existing_request_count + requests_to_add)

    @raises(Http404)
    def test_nonexistant_user(self):
        """Buying requests for nonexistant user should return a 404."""
        post_request = self.factory.post(self.url, self.data)
        post_request = mock_middleware(post_request)
        # here is the cool part: the request user is the buyer and the URL user is the recipient
        post_request.user = self.user
        self.view(post_request, 'nonexistant_user')

    def test_bad_post_data(self):
        """Bad post data should cancel the transaction."""
        existing_request_count = self.user.profile.num_requests
        bad_data = {
            'tok': 'bad'
        }
        post_request = self.factory.post(self.url, bad_data)
        post_request = mock_middleware(post_request)
        post_request.user = self.user
        self.view(post_request, self.user.username)
        self.user.profile.refresh_from_db()
        eq_(self.user.profile.num_requests, existing_request_count)


class TestAccountFunctional(TestCase):
    """Functional tests for account"""
    def setUp(self):
        self.user = UserFactory()

    def test_public_views(self):
        """Test public views while not logged in"""
        response = http_get_response(reverse('acct-login'), login)
        eq_(response.status_code, 200,
            'Login page should be publicly visible.')
        # account overview page
        response = http_get_response(reverse('accounts'), views.AccountsView.as_view())
        eq_(response.status_code, 200,
            'Top level accounts page should be publicly visible.')
        # profile page
        request_factory = RequestFactory()
        request = request_factory.get(self.user.profile.get_absolute_url())
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = views.profile(request, self.user.username)
        eq_(response.status_code, 200, 'User profiles should be publicly visible.')

    def test_unallowed_views(self):
        """Private URLs should redirect logged-out users to the log in page"""
        # pylint:disable=no-self-use
        # my profile
        get, post = http_get_post(reverse('acct-my-profile'), views.profile, {})
        eq_(get.status_code, 302, 'My profile link reponds with 302 to logged out user.')
        eq_(post.status_code, 302, 'POST to my profile link responds with 302.')
        # settings
        get, post = http_get_post(reverse('acct-settings'), views.settings, {})
        eq_(get.status_code, 302, 'GET /profile responds with 302 to logged out user.')
        eq_(post.status_code, 302, 'POST /settings reponds with 302 to logged out user.')

    def test_auth_views(self):
        """Test private views while logged in"""
        response = http_get_response(reverse('acct-my-profile'), views.profile, self.user)
        eq_(response.status_code, 200, 'Logged in user may view their own profile.')
        response = http_get_response(reverse('acct-settings'), views.settings, self.user)
        eq_(response.status_code, 200, 'Logged in user may view their own settings.')

    def test_settings_view(self):
        """Test the account settings view"""
        profile = self.user.profile
        profile_data = {
            'action': 'profile',
            'first_name': 'Allan',
            'last_name': 'Lasser',
            'twitter': 'allanlasser'
        }
        email_data = {
            'action': 'email',
            'email': 'allan@muckrock.com',
            'email_pref': 'hourly'
        }
        settings_url = reverse('acct-settings')
        http_post_response(settings_url, views.settings, profile_data, self.user)
        http_post_response(settings_url, views.settings, email_data, self.user)
        self.user.refresh_from_db()
        profile.refresh_from_db()
        all_data = {}
        all_data.update(profile_data)
        all_data.update(email_data)
        all_data.pop('action')
        for key, val in all_data.iteritems():
            if key in ['first_name', 'last_name', 'email']:
                eq_(val, getattr(self.user, key))
            else:
                eq_(val, getattr(profile, key))
