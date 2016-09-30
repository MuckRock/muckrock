"""
Tests for the FOIAMachine application.
"""

from django.test import TestCase
from django.contrib import auth

from django_hosts.resolvers import reverse
from nose.tools import eq_, ok_

from muckrock.factories import UserFactory, AgencyFactory
from muckrock.foiamachine.factories import FoiaMachineRequestFactory
from muckrock.foiamachine.models import FoiaMachineRequest
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


class TestFoiaMachineRequest(TestCase):
    """The FOIA Machine Request should store information we need to send a request."""
    def setUp(self):
        self.user = UserFactory()
        self.title = 'Test Request'
        self.request_language = 'Lorem ipsum'
        self.agency = AgencyFactory()
        self.jurisdiction = self.agency.jurisdiction
        self.foi = FoiaMachineRequestFactory(
            user=self.user,
            title=self.title,
            request_language=self.request_language,
            jurisdiction=self.jurisdiction,
        )

    def test_create_FoiaMachineRequest(self):
        """Requests should only require a user, a title,
        request language, and a jurisdiction to be created."""
        foi = FoiaMachineRequest.objects.create(
            user=self.user,
            title=self.title,
            request_language=self.request_language,
            jurisdiction=self.jurisdiction,
        )
        ok_(foi, 'The request should be created.')
        ok_(foi.slug, 'The slug should be created automatically.')

    def test_unicode(self):
        """Requests should use their titles when converted to unicode."""
        eq_(unicode(self.foi), self.foi.title,
            'The Unicode representation should be the title.')

    def test_get_absolute_url(self):
        """Request urls should include their slug and their id."""
        kwargs = {
            'slug': self.foi.slug,
            'pk': self.foi.pk,
        }
        actual_url = self.foi.get_absolute_url()
        expected_url = reverse('foi-detail', host='foiamachine', kwargs=kwargs)
        eq_(actual_url, expected_url)
