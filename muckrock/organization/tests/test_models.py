"""
Tests the models of the organization application
"""
# pylint: disable=no-member

from django.test import TestCase

import muckrock.factories

import logging
from mock import Mock, patch
import nose.tools
import stripe

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

# Creates mock items for testing methods that involve Stripe
mock_subscription = Mock()
mock_subscription.id = 'test-org-subscription'
mock_subscription.save.return_value = mock_subscription
mock_customer = Mock()
mock_customer.name = 'allan'
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


class TestRations(TestCase):
    """Test the dynamic rationing of seats, monthly cost, and monthly requests."""
    def setUp(self):
        """Create a basic organization"""
        self.org = muckrock.factories.OrganizationFactory()

    def test_no_change(self):
        """If the seats do not change, then the cost and requests shouldn't change."""
        num_seats = 0
        old_monthly_cost = self.org.monthly_cost
        old_monthly_requests = self.org.monthly_requests
        new_monthly_cost = self.org.update_monthly_cost(num_seats)
        new_monthly_requets = self.org.update_monthly_requests(num_seats)
        eq_(old_monthly_cost, new_monthly_cost,
            'The monthly cost should not change if the number of seats stays the same.')
        eq_(old_monthly_requests, new_monthly_requets,
            'The monthly requests should not change if the number of seats stays the same.')

    def test_increase(self):
        """If the seats increase, then the cost and requests should also increase."""
        seat_increase = 1
        cost_increase = 2000 * seat_increase
        request_increase = 10 * seat_increase
        num_seats = seat_increase
        old_monthly_cost = self.org.monthly_cost
        old_monthly_requests = self.org.monthly_requests
        new_monthly_cost = self.org.update_monthly_cost(num_seats)
        new_monthly_requests = self.org.update_monthly_requests(num_seats)
        eq_(new_monthly_cost, old_monthly_cost + cost_increase,
            'The monthly cost should increase based on the old cost.')
        eq_(new_monthly_requests, old_monthly_requests + request_increase,
            'The monhtly requests should increase based on the old requests.')

    def test_decrease(self):
        """If the seats decrease, then the cost and requests should also decrease."""
        seat_decrease = -1
        cost_decrease = 2000 * seat_decrease
        request_decrease = 10 * seat_decrease
        num_seats = seat_decrease
        old_monthly_cost = self.org.monthly_cost
        old_monthly_requests = self.org.monthly_requests
        new_monthly_cost = self.org.update_monthly_cost(num_seats)
        new_monthly_requests = self.org.update_monthly_requests(num_seats)
        eq_(new_monthly_cost, old_monthly_cost + cost_decrease,
            'The monthly cost should decrease based on the old cost.')
        eq_(new_monthly_requests, old_monthly_requests + request_decrease,
            'The monhtly requests should decrease based on the old requests.')


# Substitutes mock items for Stripe items in each test
@patch('stripe.Customer', MockCustomer)
@patch('stripe.Plan', MockPlan)
class TestSubscriptions(TestCase):
    """Test the methods for activating, updating, and cancelling an org subscription."""
    def setUp(self):
        """Create a basic organization"""
        self.org = muckrock.factories.OrganizationFactory()
        ok_(not self.org.active and not self.org.stripe_id,
            'By default, an org should be inactive and subscription-less')

    def test_activation(self):
        """Activating the organization should subscribe the owner to an org plan."""
        # lets add an extra seat, just to make things interesting
        seat_increase = 1
        expected_cost_increase = self.org.monthly_cost + 2000 * seat_increase
        expected_request_increase = self.org.monthly_requests + 10 * seat_increase
        expected_quantity = expected_cost_increase / 100
        self.org.activate_subscription(seat_increase)
        eq_(self.org.monthly_cost, expected_cost_increase,
            'The monthly cost should be updated.')
        eq_(self.org.monthly_requests, expected_request_increase,
            'The monthly requests should be updated.')
        eq_(self.org.stripe_id, mock_subscription.id,
            'The subscription ID should be saved to the organization.')
        ok_(self.org.active,
            'The org should be set to an active state.')

    def test_updating(self):
        """Updating the subscription should update the quantity of the subscription."""
        # change the stripe_id to something else, to make sure it gets updated
        self.org.stripe_id = 'temp'
        self.org.active = True
        self.org.save()
        # let's update this org with 2 more seats
        seat_increase = 2
        expected_cost_increase = self.org.monthly_cost + 2000 * seat_increase
        expected_request_increase = self.org.monthly_requests + 10 * seat_increase
        expected_quantity = expected_cost_increase / 100
        self.org.update_subscription(seat_increase)
        self.org.refresh_from_db()
        eq_(self.org.monthly_cost, expected_cost_increase,
            'The monthly cost should be updated.')
        eq_(self.org.monthly_requests, expected_request_increase,
            'The monthly requests should be updated.')
        eq_(mock_subscription.quantity, expected_quantity,
            'The subscription quantity should be based on the monthly cost.')
        eq_(self.org.stripe_id, mock_subscription.id,
            'The subscription ID should be saved to the organization.')
        ok_(self.org.active,
            'The org should be set to an active state.')

    def test_cancelling(self):
        """Cancelling the subscription should render the org inactive."""
        self.org.cancel_subscription()
        ok_(not self.org.active,
            'The organization should be set to an inactive state.')
        ok_(not self.org.stripe_id,
            'The stripe subscription ID should be removed from the org.')

    @nose.tools.raises(AttributeError)
    def test_update_inactive(self):
        """Updating an inactive organization should raise an error."""
        ok_(not self.org.active)
        self.org.update_subscription(1)

class TestMembership(TestCase):
    """Test the membership functions of the organization"""
    def setUp(self):
        """Create an owner, a member, and an organization"""
        self.org = muckrock.factories.OrganizationFactory()
        self.owner = self.org.owner
        self.member = muckrock.factories.UserFactory(profile__organization=self.org)

    def test_is_owned_by(self):
        """Test the is_owned_by method."""
        ok_(self.org.is_owned_by(self.owner), 'The org should correctly report its owner.')

    def test_has_member(self):
        """Test the has_member method."""
        ok_(self.org.has_member(self.member), 'The org should correctly report its members.')

    def test_add_member(self):
        """Test adding a member to the organization."""
        new_member = muckrock.factories.UserFactory()
        self.org.add_member(new_member)
        eq_(self.org, new_member.profile.organization,
            'The new member should be added to the org.')
        ok_(self.org.has_member(new_member),
            'The org should recognize the new member.')

    def test_remove_member(self):
        """Test removing a member from the organization."""
        self.org.remove_member(self.member)
        eq_(None, self.member.profile.organization,
            'The member should be removed from the org.')
        ok_(not self.org.has_member(self.member),
            'The org should not recognize the ex-member.')

    @nose.tools.raises(ValueError)
    def test_add_member_without_seat(self):
        """An exception should be raised when trying to add a member without any available seat."""
        member2 = muckrock.factories.UserFactory(profile__organization=self.org)
        member3 = muckrock.factories.UserFactory(profile__organization=self.org)
        eq_(self.org.max_users, 3,
            'The org should start with three seats.')
        eq_(self.org.members.count(), 3,
            'The org should have 3 members.')
        # adding a new member should throw an error
        self.org.add_member(muckrock.factories.UserFactory())

    @nose.tools.raises(ValueError)
    def test_remove_non_member(self):
        """
        An exception should be raised when trying to remove
        a user who is not a member from the organization.
        """
        non_member = muckrock.factories.UserFactory()
        self.org.remove_member(non_member)

    @nose.tools.raises(ValueError)
    def test_remove_owner(self):
        """An exception should be raised when trying to remove the org's owner as a member"""
        self.org.remove_member(self.owner)
