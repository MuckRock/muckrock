"""
Tests for FOIA Machine views.
"""

from django.contrib import auth
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.test import TestCase

from django_hosts.resolvers import reverse
from nose.tools import eq_, ok_, raises

from muckrock.factories import UserFactory
from muckrock.foiamachine import factories, forms, models, views
from muckrock.jurisdiction.factories import StateJurisdictionFactory
from muckrock.test_utils import http_get_response, http_post_response

class TestHomepage(TestCase):
    """The homepage should provide information about FOIAMachine and helpful links."""
    def setUp(self):
        self.view = views.Homepage.as_view()
        self.url = reverse('index', host='foiamachine')

    def test_unauthenticated(self):
        """The homepage should return 200."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 200)

    def test_authenticated(self):
        """If the user is authenticated, the homepage should redirect to their profile."""
        user = UserFactory()
        response = http_get_response(self.url, self.view, user)
        eq_(response.status_code, 302)
        eq_(response.url, reverse('profile', host='foiamachine'))


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
        self.view = views.Signup.as_view()
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
        self.view = views.Profile.as_view()
        self.url = reverse('profile', host='foiamachine')

    def test_unauthenticated(self):
        """Authentication should be required to view the profile page."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 302, 'The view should redirect.')
        eq_(response.url, reverse('login', host='foiamachine') + '?next=' + self.url,
            'The redirect should point to the login view, with this as the next view.')

    def test_authenticated(self):
        """When authenticated, the view should return 200."""
        user = UserFactory()
        response = http_get_response(self.url, self.view, user)
        eq_(response.status_code, 200)


class TestFoiaMachineRequestCreateView(TestCase):
    """Users should be able to create a new request, as long as they are logged in."""
    def setUp(self):
        self.view = views.FoiaMachineRequestCreateView.as_view()
        self.url = reverse('foi-create', host='foiamachine')
        self.user = UserFactory()

    def test_unauthenticated(self):
        """Unauthenticated users should be redirected to the login screen."""
        response = http_get_response(self.url, self.view)
        eq_(response.status_code, 302, 'The view should redirect.')
        eq_(response.url, reverse('login', host='foiamachine') + '?next=' + self.url,
            'The redirect should point to the login view, with this as the next view.')

    def test_authenticated(self):
        """When authenticated, the view should return 200."""
        user = UserFactory()
        response = http_get_response(self.url, self.view, user)
        eq_(response.status_code, 200)

    def test_create(self):
        """Posting a valid creation form should create a request and redirect to it."""
        title = 'Test Request'
        request_language = 'Lorem ipsum'
        jurisdiction = StateJurisdictionFactory().id
        form = forms.FoiaMachineRequestForm({
            'title': title,
            'request_language': request_language,
            'jurisdiction': jurisdiction
        })
        ok_(form.is_valid())
        response = http_post_response(self.url, self.view, form.data, self.user)
        eq_(response.status_code, 302, 'When successful the view should redirect to the request.')
        foi = models.FoiaMachineRequest.objects.first()
        eq_(response.url, foi.get_absolute_url())
        ok_(foi.communications.count() == 1, 'A communication should be created.')


class TestFoiaMachineRequestDetailView(TestCase):
    """Anyone can see the request, as long as they have the link."""
    def setUp(self):
        self.foi = factories.FoiaMachineRequestFactory()
        self.view = views.FoiaMachineRequestDetailView.as_view()
        self.kwargs = {
            'slug': self.foi.slug,
            'pk': self.foi.pk,
        }
        self.url = reverse('foi-detail', host='foiamachine', kwargs=self.kwargs)

    def test_get(self):
        """Anyone can see the request page."""
        response = http_get_response(self.url, self.view, **self.kwargs)
        eq_(response.status_code, 200)


class TestFoiaMachineRequestUpdateView(TestCase):
    """Only the creator of the request may update it."""
    def setUp(self):
        self.foi = factories.FoiaMachineRequestFactory()
        self.view = views.FoiaMachineRequestUpdateView.as_view()
        self.kwargs = {
            'slug': self.foi.slug,
            'pk': self.foi.pk,
        }
        self.url = reverse('foi-update', host='foiamachine', kwargs=self.kwargs)

    def test_anonymous(self):
        """Logged out users should be redirected to the login view."""
        response = http_get_response(self.url, self.view, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, (reverse('login', host='foiamachine') +
            '?next=' + reverse('foi-update', host='foiamachine', kwargs=self.kwargs)))

    def test_not_owner(self):
        """Users who are not the owner should be redirected to the FOI detail view."""
        not_owner = UserFactory()
        response = http_get_response(self.url, self.view, not_owner, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, self.foi.get_absolute_url())

    def test_owner(self):
        """The owner should be able to get the request."""
        response = http_get_response(self.url, self.view, self.foi.user, **self.kwargs)
        eq_(response.status_code, 200)

    def test_post(self):
        """Posting updated request info should update the request!"""
        new_jurisdiction = StateJurisdictionFactory()
        data = {
            'title': 'New Title',
            'request_language': 'Foo bar baz!',
            'jurisdiction': new_jurisdiction.id
        }
        form = forms.FoiaMachineRequestForm(data, instance=self.foi)
        ok_(form.is_valid())
        response = http_post_response(self.url, self.view, data, self.foi.user, **self.kwargs)
        self.foi.refresh_from_db()
        # we have to update the slug, because the title changed
        self.kwargs['slug'] = self.foi.slug
        eq_(response.status_code, 302)
        eq_(response.url, reverse('foi-detail', host='foiamachine', kwargs=self.kwargs))
        eq_(self.foi.title, data['title'])
        eq_(self.foi.request_language, data['request_language'])
        eq_(self.foi.jurisdiction, new_jurisdiction)


class TestFoiaMachineRequestDeleteView(TestCase):
    """The owner should be able to delete the request, if they really want to."""
    def setUp(self):
        self.foi = factories.FoiaMachineRequestFactory()
        self.view = views.FoiaMachineRequestDeleteView.as_view()
        self.kwargs = {
            'slug': self.foi.slug,
            'pk': self.foi.pk,
        }
        self.url = reverse('foi-delete', host='foiamachine', kwargs=self.kwargs)

    def test_anonymous(self):
        """Logged out users should be redirected to the login view."""
        response = http_get_response(self.url, self.view, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, (reverse('login', host='foiamachine') +
            '?next=' + reverse('foi-delete', host='foiamachine', kwargs=self.kwargs)))

    def test_not_owner(self):
        """Users who are not the owner should be redirected to the FOI detail view."""
        not_owner = UserFactory()
        response = http_get_response(self.url, self.view, not_owner, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, self.foi.get_absolute_url())

    def test_owner(self):
        """The owner should be able to get the request."""
        response = http_get_response(self.url, self.view, self.foi.user, **self.kwargs)
        eq_(response.status_code, 200)

    @raises(ObjectDoesNotExist)
    def test_post(self):
        """Posting updated request info should update the request!"""
        data = {}
        response = http_post_response(self.url, self.view, data, self.foi.user, **self.kwargs)
        self.foi.refresh_from_db()


class TestFoiaMachineCommunicationCreateView(TestCase):
    """The owner of the request should be able to add a communication to the request."""
    def setUp(self):
        self.foi = factories.FoiaMachineRequestFactory()
        self.view = views.FoiaMachineCommunicationCreateView.as_view()
        self.kwargs = {
            'foi_slug': self.foi.slug,
            'foi_pk': self.foi.pk,
        }
        self.url = reverse('comm-create', host='foiamachine', kwargs=self.kwargs)

    def test_anonymous(self):
        """Logged out users should be redirected to the login view."""
        response = http_get_response(self.url, self.view, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, (reverse('login', host='foiamachine') +
            '?next=' + reverse('comm-create', host='foiamachine', kwargs=self.kwargs)))

    def test_not_owner(self):
        """Users who are not the owner should be redirected to the FOI detail view."""
        not_owner = UserFactory()
        response = http_get_response(self.url, self.view, not_owner, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, self.foi.get_absolute_url())

    def test_owner(self):
        """The owner should be able to get the request."""
        response = http_get_response(self.url, self.view, self.foi.user, **self.kwargs)
        eq_(response.status_code, 200)


class TestFoiaMachineCommunicationUpdateView(TestCase):
    """The owner of the request should be able to update a communication on the request."""
    def setUp(self):
        self.comm = factories.FoiaMachineCommunicationFactory()
        self.view = views.FoiaMachineCommunicationUpdateView.as_view()
        self.kwargs = {
            'foi_slug': self.comm.request.slug,
            'foi_pk': self.comm.request.pk,
            'pk': self.comm.pk,
        }
        self.url = reverse('comm-update', host='foiamachine', kwargs=self.kwargs)

    def test_anonymous(self):
        """Logged out users should be redirected to the login view."""
        response = http_get_response(self.url, self.view, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, (reverse('login', host='foiamachine') +
            '?next=' + reverse('comm-update', host='foiamachine', kwargs=self.kwargs)))

    def test_not_owner(self):
        """Users who are not the owner should be redirected to the FOI detail view."""
        not_owner = UserFactory()
        response = http_get_response(self.url, self.view, not_owner, **self.kwargs)
        eq_(response.status_code, 302)
        eq_(response.url, self.comm.request.get_absolute_url())

    def test_owner(self):
        """The owner should be able to get the request."""
        response = http_get_response(self.url, self.view, self.comm.request.user, **self.kwargs)
        eq_(response.status_code, 200)
