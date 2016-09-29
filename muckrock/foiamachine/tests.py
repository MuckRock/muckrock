"""
Tests for the FOIAMachine application.
"""

from django.test import TestCase
from django.contrib import auth

from django_hosts.resolvers import reverse
from nose.tools import eq_, ok_

from muckrock.factories import UserFactory
from muckrock.foiamachine.views import Homepage, Signup, Profile
from muckrock.test_utils import http_get_response, http_post_response


class TestHomepage(TestCase):
    """The homepage should provide information about FOIAMachine and helpful links."""
    def setUp(self):
        self.view = Homepage.as_view()
        self.url = reverse('index', host='foiamachine')

    def test_ok(self):
        """The homepage should return 200."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 200)


class TestLogin(TestCase):
    """Users should be able to log in."""
    def setUp(self):
        self.view = auth.views.login
        self.url = reverse('login', host='foiamachine')

    def test_ok(self):
        """Login should return 200."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 200)


class TestSignup(TestCase):
    """Users should be able to sign up."""
    def setUp(self):
        self.view = Signup.as_view()
        self.url = reverse('signup', host='foiamachine')

    def test_ok(self):
        """Signup should return 200."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 200)

    def test_signup(self):
        """Posting the required information to sign up should create an account,
        log the user into the account, create a profile for their account,
        and return a redirect to the profile page."""
        data = {
            'username': 'TestUser',
            'email': 'test@email.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'test',
            'password2': 'test',
        }
        response = http_post_response(self.url, self.view, data)
        eq_(response.status_code, 302, 'The response should redirect.')
        eq_(response.url, reverse('profile', host='foiamachine'))
        user = auth.models.User.objects.get(username=data['username'])
        ok_(user, 'The user should be created.')
        ok_(user.profile, 'The user should be given a profile.')


class TestProfile(TestCase):
    """Users should be able to view their profile once they're logged in."""
    def setUp(self):
        self.view = Profile.as_view()
        self.url = reverse('profile', host='foiamachine')

    def test_unauthenticated(self):
        """Authentication should be required to view the profile page."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 302, 'The view should redirect.')
        eq_(response.url, reverse('login', host='foiamachine'),
            'The redirect should point to the login view.')

    def test_authenticated(self):
        """When authenticated, the view should return 200."""
        user = UserFactory()
        response = http_get_response(self.url, self.view, user)
        eq_(response.status_code, 200)


class TestPasswordReset(TestCase):
    """Users should be able to reset their passwords using the built-in Django functionality."""
    def setUp(self):
        self.user = UserFactory()
        self.view = auth.views.password_reset
        self.url = reverse('password-reset', host='foiamachine')

    def test_reset(self):
        data = {'email': self.user.email}
        response = http_post_response(self.url, self.view, data, self.user)
        eq_(response.status_code, 302, 'The view should redirect upon success. %s' % response.status_code)
        eq_(response.url, reverse('password-reset-done', host='foiamachine'),
            'The view should redirect to the password reset confirmation screen.')
