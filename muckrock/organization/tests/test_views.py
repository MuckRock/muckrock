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


class TestCreateView(TestCase):
    """Tests the expectations of the organization creation view."""
    def setUp(self):
        self.url = reverse('org-create')
        self.request_factory = RequestFactory()
        self.create_view = muckrock.organization.views.OrganizationCreateView.as_view()

    def test_get_ok(self):
        """Regular users should be able to create a request."""
        regular_user = muckrock.factories.UserFactory()
        request = self.request_factory.get(self.url)
        request = mock_middleware(request)
        request.user = regular_user
        response = self.create_view(request)
        eq_(response.status_code, 200,
            'Regular users should be able to create an organization.')
        ok_(isinstance(response.context_data['form'], muckrock.organization.forms.CreateForm),
            'Regular users should be shown the regular creation form.')

    def test_get_forbidden(self):
        """Users who already own an organization should be denied access."""
        org = muckrock.factories.OrganizationFactory()
        request = self.request_factory.get(self.url)
        request = mock_middleware(request)
        request.user = org.owner
        response = self.create_view(request)
        eq_(response.status_code, 302,
            'Existing owners should not be allowed to create another organization.')

    def test_staff_get(self):
        """Staff should be able to create an org even if they own a different one."""
        staff_user = muckrock.factories.UserFactory(is_staff=True)
        muckrock.factories.OrganizationFactory(owner=staff_user)
        request = self.request_factory.get(self.url)
        request = mock_middleware(request)
        request.user = staff_user
        response = self.create_view(request)
        eq_(response.status_code, 200,
            'Staff should be allowed to create an organization even if they already own one.')
        ok_(isinstance(response.context_data['form'], muckrock.organization.forms.StaffCreateForm),
            'Staff should be shown a special staff-only creation form.')

    def test_post_ok(self):
        """
        Regular users should be able to activate an org.
        When doing so, they should be made the owner.
        """
        regular_user = muckrock.factories.UserFactory()
        org_name = 'Cool Org'
        data = {'name': org_name}
        form = muckrock.organization.forms.CreateForm(data)
        ok_(form.is_valid(), '%s' % form.errors)
        request = self.request_factory.post(self.url, data)
        request = mock_middleware(request)
        request.user = regular_user
        response = self.create_view(request)
        org = muckrock.organization.models.Organization.objects.get(name=org_name)
        ok_(org,
            'The organization should be created.')
        ok_(not org.active,
            'The organization should be inactive.')
        eq_(org.owner, regular_user,
            'The user should be made the owner of the organization.')
        eq_(response.status_code, 302,
            'The user should be redirected to the activation page when creation is successful.')

    def test_staff_post(self):
        """Staff users should need to provide more information, including an owner."""
        staff_user = muckrock.factories.UserFactory(is_staff=True)
        org_owner = muckrock.factories.UserFactory()
        org_name = 'Cool Org'
        org_max = 3
        org_cost = 10000
        org_requests = 50
        data = {
            'name': org_name,
            'owner': org_owner.pk,
            'max_users': org_max,
            'monthly_cost': org_cost,
            'monthly_requests': org_requests
        }
        form = muckrock.organization.forms.StaffCreateForm(data)
        ok_(form.is_valid(), '%s' % form.errors)
        request = self.request_factory.post(self.url, data)
        request = mock_middleware(request)
        request.user = staff_user
        response = self.create_view(request)
        eq_(response.status_code, 302,
            'The user should be redirected to the activation page when creation is successful.')
        org = muckrock.organization.models.Organization.objects.get(name=org_name)
        ok_(org,
            'The organization should be created.')
        ok_(not org.active,
            'The organization should be inactive.')
        eq_(org.owner, org_owner,
            'The organization should have an owner assigned to it.')
        eq_(org.max_users, org_max,
            'The organization should have its max users set.')
        eq_(org.monthly_cost, org_cost,
            'The organization should have its monthly cost set.')
        eq_(org.monthly_requests, org_requests,
            'The organization should have its monthly requests set.')


class TestActivateView(TestCase):
    """Test the expectations of organization activation"""
    def setUp(self):
        self.org = muckrock.factories.OrganizationFactory()
        self.request_factory = RequestFactory()
        self.url = reverse('org-activate', kwargs={'slug': self.org.slug})
        self.view = muckrock.organization.views.OrganizationActivateView.as_view()

    def test_regular_get(self):
        """Regular users should be denied access to the activation view."""
        request = self.request_factory.get(self.url)
        request = mock_middleware(request)
        request.user = muckrock.factories.UserFactory()
        response = self.view(request, slug=self.org.slug)
        eq_(response.status_code, 302)

    def test_owner_get(self):
        """Organization owners should be allowed access to the activation view."""
        request = self.request_factory.get(self.url)
        request = mock_middleware(request)
        request.user = self.org.owner
        response = self.view(request, slug=self.org.slug)
        eq_(response.status_code, 200)

    def test_staff_get(self):
        """Staff should be allowed access to the activation view."""
        request = self.request_factory.get(self.url)
        request = mock_middleware(request)
        request.user = muckrock.factories.UserFactory(is_staff=True)
        response = self.view(request, slug=self.org.slug)
        eq_(response.status_code, 200)

    def test_active_get(self):
        """An active organization should deny all access to its activation view."""
        self.org.active = True
        self.org.save()
        request = self.request_factory.get(self.url)
        request = mock_middleware(request)
        request.user = self.org.owner
        response = self.view(request, slug=self.org.slug)
        eq_(response.status_code, 302)

    @patch('muckrock.organization.models.Organization.activate_subscription')
    def test_post_ok(self, mock_activation):
        """Posting a valid Stripe token and the number of seats should activate the organization."""
        logging.debug(self.org.max_users)
        data = {'token': 'test', 'max_users': self.org.max_users}
        request = self.request_factory.post(self.url, data)
        request = mock_middleware(request)
        request.user = self.org.owner
        response = self.view(request, slug=self.org.slug)
        self.org.refresh_from_db()
        eq_(response.status_code, 302,
            'The view should redirect to the org page on success.')
        ok_(mock_activation.called,
            'The organization should be activated! That\'s the whole point!')


class TestDeactivateView(TestCase):
    """Only staff and owners should be allowed to POST to the deactivation view."""
    def setUp(self):
        # create an org with a plan, so we can cancel it
        self.org = muckrock.factories.OrganizationFactory(active=True)
        self.request_factory = RequestFactory()
        self.url = reverse('org-deactivate', kwargs={'slug': self.org.slug})
        self.request = self.request_factory.post(self.url)
        self.request = mock_middleware(self.request)
        self.view = muckrock.organization.views.deactivate_organization

    @patch('muckrock.organization.models.Organization.cancel_subscription')
    def test_regular_post(self, mock_cancellation):
        """Regular users should be denied the ability to POST."""
        self.request.user = muckrock.factories.UserFactory()
        self.view(self.request, self.org.slug)
        ok_(not mock_cancellation.called)

    @patch('muckrock.organization.models.Organization.cancel_subscription')
    def test_owner_post(self, mock_cancellation):
        """Owners should be able to cancel the subscription."""
        self.request.user = self.org.owner
        self.view(self.request, self.org.slug)
        ok_(mock_cancellation.called)

    @patch('muckrock.organization.models.Organization.cancel_subscription')
    def test_staff_post(self, mock_cancellation):
        """Staff should be able to cancel the subscription."""
        self.request.user = muckrock.factories.UserFactory(is_staff=True)
        self.view(self.request, self.org.slug)
        ok_(mock_cancellation.called)

    @patch('muckrock.organization.models.Organization.cancel_subscription')
    def test_inactive_post(self, mock_cancellation):
        """Should not cancel the subscription if the org is already inactive."""
        self.org.active = False
        self.org.save()
        self.request.user = self.org.owner
        self.view(self.request, self.org.slug)
        ok_(not mock_cancellation.called)
