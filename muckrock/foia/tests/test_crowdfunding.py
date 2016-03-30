"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse, resolve
from django.test import TestCase, RequestFactory
import nose.tools

import datetime

from muckrock.crowdfund.models import Crowdfund
from muckrock.factories import UserFactory, FOIARequestFactory
from muckrock.foia.views import crowdfund_request
from muckrock.utils import mock_middleware

# pylint: disable=missing-docstring
# pylint: disable=invalid-name

class TestFOIACrowdfunding(TestCase):
    """Tests for FOIA Crowdfunding"""
    def setUp(self):
        self.foia = FOIARequestFactory(status='payment')
        self.url = reverse('foia-crowdfund', args=(
            self.foia.jurisdiction.slug,
            self.foia.jurisdiction.id,
            self.foia.slug,
            self.foia.id))
        self.request_factory = RequestFactory()
        self.view = crowdfund_request

    def get_res(self, user):
        """Returns a GET response from the endpoint."""
        if user is None:
            user = AnonymousUser()
        request = self.request_factory.get(self.url)
        request.user = user
        request = mock_middleware(request)
        return self.view(request, self.foia.pk)

    def post_res(self, user, data):
        """Returns a POST response from the endpoint."""
        if user is None:
            user = AnonymousUser()
        request = self.request_factory.post(self.url, data)
        request.user = user
        request = mock_middleware(request)
        return self.view(request, self.foia.pk)

    def test_crowdfund_url(self):
        """Crowdfund creation should use the /crowdfund endpoint of a request."""
        expected_url = (
            '/foi/' +
            self.foia.jurisdiction.slug + '-' + str(self.foia.jurisdiction.id) + '/' +
            self.foia.slug + '-' + str(self.foia.id) +
            '/crowdfund/'
        )
        nose.tools.eq_(self.url, expected_url,
            'Crowdfund URL <' + self.url + '> should match expected URL <' + expected_url + '>')

    def test_crowdfund_view(self):
        """The url should actually resolve to a view."""
        resolver = resolve(self.url)
        nose.tools.eq_(resolver.view_name, 'foia-crowdfund',
            'Crowdfund view name "' + resolver.view_name + '" should match "foia-crowdfund"')

    def test_crowdfund_view_requires_login(self):
        """Logged out users should be redirected to the login page"""
        response = self.get_res(None)
        nose.tools.ok_(response.status_code, 302)
        nose.tools.eq_(response.url, '/accounts/login/?next=%s' % self.url)

    def test_crowdfund_view_allows_owner(self):
        """Request owners may create a crowdfund on their request."""
        response = self.get_res(self.foia.user)
        nose.tools.eq_(response.status_code, 200,
            ('Above all else crowdfund should totally respond with a 200 OK if'
            ' logged in user owns the request. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_requires_owner(self):
        """Users who are not the owner cannot start a crowdfund on a request."""
        not_owner = UserFactory()
        response = self.get_res(not_owner)
        nose.tools.eq_(response.status_code, 302,
            ('Crowdfund should respond with a 302 redirect if logged in'
            ' user is not the owner. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_allows_staff(self):
        """Staff members are the exception to the above rule, they can do whatevs."""
        staff_user = UserFactory(is_staff=True)
        response = self.get_res(staff_user)
        nose.tools.eq_(response.status_code, 200,
            ('Crowdfund should respond with a 200 OK if logged in user'
            ' is a staff member. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_crowdfund_already_exists(self):
        """A crowdfund cannot be created for a request that already has one, even if expired."""
        date_due = datetime.datetime.now() + datetime.timedelta(30)
        self.foia.crowdfund = Crowdfund.objects.create(date_due=date_due)
        self.foia.save()
        response = self.get_res(self.foia.user)
        nose.tools.eq_(response.status_code, 302,
            ('If a request already has a crowdfund, trying to create a new one '
            'should respond with 302 status code. (Responds with %d)' % response.status_code))

    def test_crowdfund_view_payment_not_required(self):
        """A crowdfund can only be created for a request with a status of 'payment'"""
        self.foia.status = 'submitted'
        self.foia.save()
        response = self.get_res(self.foia.user)
        nose.tools.eq_(response.status_code, 302,
            ('If a request does not have a "Payment Required" status, should '
            'respond with a 302 status code. (Responds with %d)' % response.status_code))

    def test_crowdfund_creation(self):
        """Creating a crowdfund should associate it with the request."""
        name = 'Request Crowdfund'
        description = 'A crowdfund'
        payment_required = 100
        payment_capped = True
        date_due = datetime.date.today() + datetime.timedelta(20)
        data = {
            'name': name,
            'description': description,
            'payment_required': payment_required,
            'payment_capped': payment_capped,
            'date_due': date_due
        }
        response = self.post_res(self.foia.user, data)
        nose.tools.eq_(response.status_code, 302, 'The request should redirect to the FOIA.')
        self.foia.refresh_from_db()
        nose.tools.ok_(self.foia.has_crowdfund(),
            'The crowdfund should be created and associated with the FOIA.')
