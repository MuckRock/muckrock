"""
Test organization view classes and functions
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

import logging
from mock import Mock, patch
from nose.tools import ok_, eq_

from muckrock.accounts.models import Profile
import muckrock.factories
from muckrock.organization.forms import OrganizationCreateForm
from muckrock.organization.views import OrganizationCreateView, activate_organization

# Creates mock items for testing methods that involve Stripe
mock_customer = Mock()
MockCustomer = Mock()
MockCustomer.create.return_value = mock_customer
MockCustomer.retrieve.return_value = mock_customer
mock_plan = Mock()
mock_plan.amount = 45000
mock_plan.name = 'Test Organization Plan'
mock_plan.id = 'test-organization-org-plan'
MockPlan = Mock()
MockPlan.create.return_value = mock_plan
MockPlan.retrieve.return_value = mock_plan

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


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Plan', MockPlan)
class TestOrgActivation(TestCase):
    """Test the expectations of organization activation"""
    def setUp(self):
        self.org = muckrock.factories.OrganizationFactory()
        request_factory = RequestFactory()
        url = reverse('org-activate', kwargs={'slug': self.org.slug})
        data = {'token': 'test'}
        self.request = request_factory.post(url, data)
        self.request = mockMiddleware(self.request)

    def test_activation(self):
        """
        When activating the organization, a Stripe plan should be created and
        the owner should be subscribed to the plan.
        """
        self.request.user = muckrock.factories.UserFactory(is_staff=True)
        response = activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.is_active())

    def test_staff_activation(self):
        """Staff should be able to activate the org."""
        self.request.user = muckrock.factories.UserFactory(is_staff=True)
        response = activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.is_active())

    def test_owner_activation(self):
        """Owner should be able to activate the org."""
        self.request.user = self.org.owner
        response = activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.is_active())

    def test_member_activation(self):
        """Members should not be able to activate the org."""
        member = muckrock.factories.UserFactory(is_staff=False)
        self.org.add_member(member)
        self.request.user = member
        response = activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(not self.org.is_active())

    def test_already_active(self):
        """An already-active org should not be able to be activated."""
        # first activate the org
        self.request.user = self.org.owner
        response = activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.is_active())
        # then try activating again, make sure the stripe id is the same
        stripe_id = self.org.stripe_id
        logging.debug(stripe_id)
        response = activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        eq_(self.org.stripe_id, stripe_id)


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Plan', MockPlan)
class TestOrgDeactivation(TestCase):
    """Test the expectations of organization deactivation"""
    def setUp(self):
        # create an org with a plan, so we can cancel it
        self.org = muckrock.factories.OrganizationFactory()
        self.activateOrganization()
        request_factory = RequestFactory()
        url = reverse('org-deactivate', kwargs={'slug': self.org.slug})
        self.request = request_factory.post(url)
        self.request = mockMiddleware(self.request)

    def activateOrganization(self):
        """Helper function to activate an organization"""
        self.org = muckrock.factories.OrganizationFactory()
        request_factory = RequestFactory()
        url = reverse('org-activate', kwargs={'slug': self.org.slug})
        data = {'token': 'test'}
        request = request_factory.post(url, data)
        request = mockMiddleware(request)
        request.user = self.org.owner
        response = activate_organization(request, self.org.slug)
        self.org.refresh_from_db()
        eq_(response.status_code, 200)
        ok_(self.org.is_active())

    def test_deactivation(self):
        """
        When deactivating the organization, the owner should be unsubscribed from
        the org's plan but the plan should not be deleted.
        """
        self.request.user = self.org.owner
        response = deactivate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(not self.org.is_active())
        ok_(self.org.stripe_id)

    def test_already_inactive(self):
        """An already-inactive org should not be able to be deactivated."""
        ok_(False, 'Test unwritten.')
