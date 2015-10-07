"""
Tests the models of the organization application
"""

from django.contrib.auth.models import User
from django.test import TestCase

from muckrock.accounts.models import Profile
import muckrock.factories
from muckrock.organization.models import Organization

from datetime import datetime
from mock import Mock, patch
import nose.tools
import stripe

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

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
# Substitutes mock items for Stripe items in each test
@patch('stripe.Customer', MockCustomer)
@patch('stripe.Plan', MockPlan)
class OrganizationPaymentTests(TestCase):
    """Test the methods that create and destroy payments and plans"""
    # pylint: disable=no-self-use

    def setUp(self):
        """Set up models for the organization"""
        self.org = muckrock.factories.OrganizationFactory()

    def test_create_plan(self):
        """Should create a plan and assign a value to the org's stripe_id field"""
        self.org.create_plan()
        nose.tools.assert_true(self.org.stripe_id)

    def test_delete_plan(self):
        """Should delete the org's plan and set stripe_id to None"""
        self.org.create_plan()
        self.org.delete_plan()
        nose.tools.assert_false(self.org.stripe_id)

    def test_update_plan(self):
        """
        Should create an org plan at once price point, then update the org's
        plan to a new price point.
        """
        self.org.create_plan()
        plan = stripe.Plan.retrieve(self.org.stripe_id)
        nose.tools.eq_(plan.amount, self.org.monthly_cost)
        self.org.monthly_cost = 15000
        mock_plan.amount = 15000
        self.org.update_plan()
        plan = stripe.Plan.retrieve(self.org.stripe_id)
        nose.tools.eq_(plan.amount, self.org.monthly_cost)

    @nose.tools.raises(ValueError)
    def test_double_create_plan(self):
        """Should return an error after trying to create a plan twice in a row"""
        self.org.create_plan()
        self.org.create_plan()

    @nose.tools.raises(ValueError)
    def test_delete_nonexistant_plan(self):
        """Should return an error after trying to delete a plan that doesn't exist"""
        self.org.delete_plan()

    @nose.tools.raises(ValueError)
    def test_update_nonexistant_plan(self):
        """Should return an error after tying to update a plan that doesn't exist"""
        self.org.update_plan()

    def test_start_subscription(self):
        """
        Should subscribe owner to the organization's plan,
        set the org to active, and reduce pro owners to community accounts
        """
        profile = self.org.owner.profile
        profile.acct_type = 'pro'
        self.org.create_plan()
        self.org.start_subscription()
        # customer = org.owner.profile.customer()
        # test if subscription was activated
        nose.tools.eq_(profile.acct_type, 'community')
        nose.tools.assert_true(self.org.active)

    def test_pause_subscription(self):
        """Should cancel owner's subscription and set the org to inactive"""
        self.org.create_plan()
        self.org.start_subscription()
        self.org.pause_subscription()
        # customer = org.owner.profile.customer()
        # test if subscription was paused
        nose.tools.assert_false(self.org.active)

class TestOrgMembership(TestCase):
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

    def test_owner_is_member(self):
        """Org should recognize owners as members."""
        ok_(not self.org.has_member(self.owner), 'The org should recognize its owner as a member.')

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
