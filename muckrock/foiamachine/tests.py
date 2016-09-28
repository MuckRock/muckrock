"""
Tests for the FOIAMachine application.
"""

from django.test import TestCase
from django.contrib import auth

from django_hosts.resolvers import reverse
from nose.tools import eq_

from muckrock.factories import UserFactory
from muckrock.foiamachine.views import Homepage, Signup, Profile
from muckrock.test_utils import http_get_response


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
