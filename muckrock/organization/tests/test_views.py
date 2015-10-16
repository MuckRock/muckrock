"""
Test organization view classes and functions
"""
# pylint: disable=no-member

from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

import logging
from mock import Mock, patch
from nose.tools import ok_, eq_

import muckrock.factories
import muckrock.organization

# Creates mock items for testing methods that involve Stripe
mock_subscription = Mock()
mock_subscription.id = 'test-org-subscription'
mock_subscription.save.return_value = mock_subscription
mock_customer = Mock()
mock_customer.subscriptions.create.return_value = mock_subscription
mock_customer.subscriptions.retrieve.return_value = mock_subscription
MockCustomer = Mock()
MockCustomer.create.return_value = mock_customer
MockCustomer.retrieve.return_value = mock_customer
mock_plan = Mock()
mock_plan.amount = 100
mock_plan.name = 'Organization'
mock_plan.id = 'org'
MockPlan = Mock()
MockPlan.create.return_value = mock_plan
MockPlan.retrieve.return_value = mock_plan

def mock_middleware(request):
    """Mocks the request with messages and session middleware"""
    setattr(request, 'session', Mock())
    setattr(request, '_messages', Mock())
    return request


class TestOrgCreate(TestCase):
    """Test the expectations of organization creation"""
    def setUp(self):
        self.url = reverse('org-create')
        self.request_factory = RequestFactory()
        self.create_view = muckrock.organization.views.OrganizationCreateView.as_view()

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
        self.request = mock_middleware(self.request)

    def test_activation(self):
        """
        When activating the organization, a Stripe plan should be created and
        the owner should be subscribed to the plan.
        """
        self.request.user = muckrock.factories.UserFactory(is_staff=True)
        muckrock.organization.views.activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.active)

    def test_staff_activation(self):
        """Staff should be able to activate the org."""
        self.request.user = muckrock.factories.UserFactory(is_staff=True)
        muckrock.organization.views.activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.active)

    def test_owner_activation(self):
        """Owner should be able to activate the org."""
        self.request.user = self.org.owner
        muckrock.organization.views.activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.active)

    def test_member_activation(self):
        """Members should not be able to activate the org."""
        member = muckrock.factories.UserFactory(is_staff=False)
        self.org.add_member(member)
        self.request.user = member
        muckrock.organization.views.activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(not self.org.active)

    def test_already_active(self):
        """An already-active org should not be able to be activated."""
        # first activate the org
        self.request.user = self.org.owner
        muckrock.organization.views.activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.active)
        # then try activating again, make sure the stripe id is the same
        stripe_id = self.org.stripe_id
        logging.debug(stripe_id)
        muckrock.organization.views.activate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        eq_(self.org.stripe_id, stripe_id)


@patch('stripe.Customer', MockCustomer)
@patch('stripe.Plan', MockPlan)
class TestOrgDeactivation(TestCase):
    """Test the expectations of organization deactivation"""
    def setUp(self):
        # create an org with a plan, so we can cancel it
        self.org = muckrock.factories.OrganizationFactory(active=True, stripe_id='test')
        ok_(self.org.active and self.org.stripe_id)
        request_factory = RequestFactory()
        url = reverse('org-deactivate', kwargs={'slug': self.org.slug})
        self.request = request_factory.post(url)
        self.request = mock_middleware(self.request)

    def test_deactivation(self):
        """
        When deactivating the organization, the owner should be unsubscribed from
        the org's plan but the plan should not be deleted.
        """
        self.request.user = self.org.owner
        muckrock.organization.views.deactivate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(not self.org.active and self.org.stripe_id)

    def test_staff_dactivation(self):
        """Staff should be able to deactivate the org."""
        self.request.user = muckrock.factories.UserFactory(is_staff=True)
        muckrock.organization.views.deactivate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(not self.org.active and self.org.stripe_id)

    def test_owner_deactivation(self):
        """Owners should able to deactivate their org."""
        self.request.user = self.org.owner
        muckrock.organization.views.deactivate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(not self.org.active and self.org.stripe_id)

    def test_member_deactivation(self):
        """Members should not be able to deactivate orgs."""
        member = muckrock.factories.UserFactory()
        self.org.add_member(member)
        self.request.user = member
        muckrock.organization.views.deactivate_organization(self.request, self.org.slug)
        self.org.refresh_from_db()
        ok_(self.org.active)

    @patch('muckrock.organization.views.Organization.pause_subscription')
    def test_already_inactive(self, pause_mock):
        """An already-inactive org should not be able to be deactivated."""
        # pylint: disable=no-self-use
        org = muckrock.factories.OrganizationFactory()
        url = reverse('org-deactivate', kwargs={'slug': org.slug})
        request = RequestFactory().post(url)
        request = mock_middleware(request)
        request.user = org.owner
        muckrock.organization.views.deactivate_organization(request, org.slug)
        ok_(not pause_mock.called)
