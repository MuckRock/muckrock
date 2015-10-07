"""
Test organization view classes and functions
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

import logging
from mock import Mock
from nose.tools import ok_, eq_

from muckrock.accounts.models import Profile
import muckrock.factories
from muckrock.organization.forms import OrganizationCreateForm
from muckrock.organization.views import OrganizationCreateView

def mockMiddleware(request):
    """Mocks the request with messages and session middleware"""
    setattr(request, 'session', Mock())
    setattr(request, '_messages', Mock())
    return request

class TestOrgCreate(TestCase):
    """Test the expectations of organization creation"""
    def setUp(self):
        self.url = reverse('org-create')
        self.request_factory = RequestFactory()
        self.create_view = OrganizationCreateView.as_view()

    def test_staff_only(self):
        """Only MuckRock staff may create a new organization."""
        request = self.request_factory.get(self.url)
        # test for nonstaff user
        request.user = muckrock.factories.UserFactory(is_staff=False)
        response = self.create_view(request)
        eq_(response.status_code, 302, 'Nonstaff users should be redirected.')
        # test for staff user
        request.user = muckrock.factories.UserFactory(is_staff=True)
        response = self.create_view(request)
        eq_(response.status_code, 200, 'Staff users should be allowed access.')

    def test_owner_is_member(self):
        """The organization owner should be saved as a member."""
        owner = muckrock.factories.UserFactory()
        form = OrganizationCreateForm({
            'name': 'Cool Org',
            'owner': owner.pk,
            'monthly_cost': 1000,
            'monthly_requests': 100,
            'max_users': 20
        })
        ok_(form.is_valid(),
            'The form should validate. Form errors: %s' % form.errors.as_json)
        request = self.request_factory.post(self.url, form.data)
        request = mockMiddleware(request)
        # for the moment, only staff can create an organization
        request.user = muckrock.factories.UserFactory(is_staff=True)
        response = OrganizationCreateView.as_view()(request)
        owner.profile.refresh_from_db()
        eq_(response.status_code, 302,
            'The view should redirect on success.')
        ok_(owner.profile.organization,
            'The owner should be assigned an organization.')
        eq_(owner.profile.organization.name, 'Cool Org',
            'The owner should be made a member of the org.')

class TestOrgActivation(TestCase):
    """Test the expectations of organization activation"""

    def test_activation(self):
        """
        When activating the organization, a Stripe plan should be created and
        the owner should be subscribed to the plan.
        """
        ok_(False, 'Test unwritten.')

    def test_staff_or_owner_only(self):
        """Only MuckRock staff or the organization owner may activate the org."""
        ok_(False, 'Test unwritten.')

    def test_already_active(self):
        """An already-active org should not be able to be activated."""
        ok_(False, 'Test unwritten.')

class TestOrgDeactivation(TestCase):
    """Test the expectations of organization deactivation"""

    def test_deactivation(self):
        """
        When deactivating the organization, the owner should be unsubscribed from
        the org's plan but the plan should not be deleted.
        """
        ok_(False, 'Test unwritten.')

    def test_staff_or_owner_only(self):
        """Only MuckRock staff or the organization owner may deactivate the org."""
        ok_(False, 'Test unwritten.')

    def test_already_inactive(self):
        """An already-inactive org should not be able to be deactivated."""
        ok_(False, 'Test unwritten.')
