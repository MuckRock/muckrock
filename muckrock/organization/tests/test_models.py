"""
Tests the models of the organization application
"""

# Django
from django.conf import settings
from django.test import TestCase

# Third Party
import nose.tools
from mock import Mock, patch

# MuckRock
import muckrock.factories
from muckrock.utils import get_stripe_token

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

# Creates mock items for testing methods that involve Stripe
mock_subscription = Mock()
mock_subscription.id = 'test-org-subscription'
mock_subscription.save.return_value = mock_subscription
mock_customer = Mock()
mock_customer.save.return_value = mock_customer
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
mock_get_customer = Mock()
mock_get_customer.return_value = mock_customer


class TestRations(TestCase):
    """Test the dynamic rationing of seats, monthly cost, and monthly requests."""

    def setUp(self):
        """Create a basic organization"""
        self.org = muckrock.factories.OrganizationFactory()

    def test_no_change(self):
        """If the seats do not change, then the cost and requests shouldn't change."""
        num_seats = self.org.max_users
        old_monthly_cost = self.org.monthly_cost
        old_monthly_requests = self.org.monthly_requests
        self.org.update_num_seats(num_seats)
        eq_(
            self.org.monthly_cost, old_monthly_cost,
            'The monthly cost should not change if the number of seats stays the same.'
        )
        eq_(
            self.org.monthly_requests, old_monthly_requests,
            'The monthly requests should not change if the number of seats stays the same.'
        )

    def test_increase(self):
        """If the seats increase, then the cost and requests should also increase."""
        seat_increase = 1
        cost_increase = settings.ORG_PRICE_PER_SEAT * seat_increase
        request_increase = settings.ORG_REQUESTS_PER_SEAT * seat_increase
        num_seats = self.org.max_users + seat_increase
        old_monthly_cost = self.org.monthly_cost
        old_monthly_requests = self.org.monthly_requests
        self.org.update_num_seats(num_seats)
        eq_(
            self.org.monthly_cost, old_monthly_cost + cost_increase,
            'The monthly cost should increase based on the old cost.'
        )
        eq_(
            self.org.monthly_requests, old_monthly_requests + request_increase,
            'The monhtly requests should increase based on the old requests.'
        )

    def test_decrease(self):
        """If the seats decrease, then the cost and requests should also decrease."""
        seat_decrease = -1
        cost_decrease = settings.ORG_PRICE_PER_SEAT * seat_decrease
        request_decrease = settings.ORG_REQUESTS_PER_SEAT * seat_decrease
        num_seats = self.org.max_users + seat_decrease
        old_monthly_cost = self.org.monthly_cost
        old_monthly_requests = self.org.monthly_requests
        self.org.update_num_seats(num_seats)
        eq_(
            self.org.monthly_cost, old_monthly_cost + cost_decrease,
            'The monthly cost should decrease based on the old cost.'
        )
        eq_(
            self.org.monthly_requests, old_monthly_requests + request_decrease,
            'The monhtly requests should decrease based on the old requests.'
        )


# Substitutes mock items for Stripe items in each test
@patch('muckrock.accounts.models.Profile.customer', mock_get_customer)
@patch('stripe.Customer', MockCustomer)
@patch('stripe.Plan', MockPlan)
class TestSubscriptions(TestCase):
    """Test the methods for activating, updating, and cancelling an org subscription."""

    def setUp(self):
        """Create a basic organization"""
        self.org = muckrock.factories.OrganizationFactory()
        ok_(
            not self.org.active and not self.org.stripe_id,
            'By default, an org should be inactive and subscription-less'
        )

    def test_activation(self):
        """Activating the organization should subscribe the owner to an org plan."""
        # pylint: disable=line-too-long
        # pylint disabled because 1 character r u kidding me
        # lets add an extra seat, just to make things interesting
        seat_increase = 1
        expected_cost_increase = self.org.monthly_cost + settings.ORG_PRICE_PER_SEAT * seat_increase
        expected_request_increase = self.org.monthly_requests + settings.ORG_REQUESTS_PER_SEAT * seat_increase
        num_seats = self.org.max_users + seat_increase
        self.org.activate_subscription('test', num_seats)
        self.org.refresh_from_db()
        eq_(
            self.org.max_users, num_seats,
            'The maximum number of users should be updated.'
        )
        eq_(
            self.org.monthly_cost, expected_cost_increase,
            'The monthly cost should be updated.'
        )
        eq_(
            self.org.monthly_requests, expected_request_increase,
            'The monthly requests should be updated.'
        )
        eq_(
            self.org.num_requests, self.org.monthly_requests,
            'The org should be granted its monthly request allotment.'
        )
        eq_(
            self.org.stripe_id, mock_subscription.id,
            'The subscription ID should be saved to the organization.'
        )
        ok_(self.org.active, 'The org should be set to an active state.')
        eq_(
            self.org.owner.profile.subscription_id, mock_subscription.id,
            'The subscription ID should also be saved to the user.'
        )

    def test_activate_as_pro(self):
        """A pro user should have their pro subscription cancelled in favor of an organization."""
        pro = muckrock.factories.ProfileFactory(
            acct_type='pro', subscription_id='test-pro'
        )
        self.org.owner = pro.user
        self.org.activate_subscription('test', self.org.max_users)
        pro.refresh_from_db()
        eq_(pro.acct_type, 'basic')
        eq_(pro.subscription_id, mock_subscription.id)

    @nose.tools.raises(ValueError)
    def test_activate_min_seats(self):
        """Activating with less than the minimum number of seats should raise an error."""
        self.org.activate_subscription('test', settings.ORG_MIN_SEATS - 1)

    @nose.tools.raises(AttributeError)
    def test_activate_active_org(self):
        """Activating and active organization should raise an error."""
        self.org.active = True
        self.org.save()
        self.org.activate_subscription('test', settings.ORG_MIN_SEATS)

    def test_updating(self):
        """Updating the subscription should update the quantity of the subscription."""
        # pylint: disable=line-too-long
        # pylint disabled because 1 character r u kidding me
        # change the stripe_id to something else, to make sure it gets updated
        self.org.stripe_id = 'temp'
        self.org.active = True
        self.org.save()
        self.org.owner.profile.subscription_id = 'temp'
        self.org.owner.profile.save()
        # let's update this org with 2 more seats
        seat_increase = 2
        expected_cost_increase = self.org.monthly_cost + settings.ORG_PRICE_PER_SEAT * seat_increase
        expected_request_increase = self.org.monthly_requests + settings.ORG_REQUESTS_PER_SEAT * seat_increase
        expected_request_count = self.org.num_requests + settings.ORG_REQUESTS_PER_SEAT * seat_increase
        expected_quantity = expected_cost_increase / 100
        num_seats = self.org.max_users + seat_increase
        self.org.update_subscription(num_seats)
        self.org.refresh_from_db()
        self.org.owner.profile.refresh_from_db()
        eq_(self.org.monthly_cost, expected_cost_increase)
        eq_(self.org.monthly_requests, expected_request_increase)
        eq_(self.org.num_requests, expected_request_count)
        eq_(self.org.max_users, num_seats)
        eq_(mock_subscription.quantity, expected_quantity)
        eq_(self.org.stripe_id, mock_subscription.id)
        eq_(self.org.owner.profile.subscription_id, mock_subscription.id)
        ok_(self.org.active)

    @nose.tools.raises(ValueError)
    def test_update_min_seats(self):
        """Activating with less than the minimum number of seats should raise an error."""
        self.org.active = True
        self.org.save()
        self.org.update_subscription(settings.ORG_MIN_SEATS - 1)

    @nose.tools.raises(AttributeError)
    def test_update_inactive(self):
        """Updating an inactive organization should raise an error."""
        ok_(not self.org.active)
        self.org.update_subscription(settings.ORG_MIN_SEATS)

    def test_cancelling(self):
        """Cancelling the subscription should render the org inactive."""
        self.org.active = True
        self.org.stripe_id = 'temp'
        self.org.save()
        self.org.owner.profile.subscription_id = 'temp'
        self.org.owner.profile.save()
        self.org.cancel_subscription()
        ok_(
            not self.org.active,
            'The organization should be set to an inactive state.'
        )
        ok_(
            not self.org.stripe_id,
            'The stripe subscription ID should be removed from the org.'
        )
        ok_(
            not self.org.owner.profile.subscription_id,
            'The Stripe subscription ID should be removed form the owner.'
        )

    @nose.tools.raises(AttributeError)
    def test_cancel_inactive(self):
        """Cancelling an inactive subscription should throw an error."""
        ok_(not self.org.active)
        self.org.cancel_subscription()


# actually tests Stripe code
class TestStripeIntegration(TestCase):
    """
    Test Stripe integration for activate, update, and cancel methods.
    Mainly checking for errors on calls to SDK methods.
    """

    def setUp(self):
        self.org = muckrock.factories.OrganizationFactory()
        self.token = get_stripe_token()

    @nose.tools.nottest
    def test_methods(self):
        """Test the subscription methods."""
        self.org.activate_subscription(self.token, self.org.max_users)
        self.org.update_subscription(self.org.max_users + 1)
        self.org.cancel_subscription()


class TestMembership(TestCase):
    """Test the membership functions of the organization"""

    def setUp(self):
        """Create an owner, a member, and an organization"""
        self.org = muckrock.factories.OrganizationFactory(active=True)
        self.owner = self.org.owner
        self.member = muckrock.factories.UserFactory(
            profile__organization=self.org
        )

    def test_is_owned_by(self):
        """Test the is_owned_by method."""
        ok_(
            self.org.is_owned_by(self.owner),
            'The org should correctly report its owner.'
        )

    def test_has_member(self):
        """Test the has_member method."""
        ok_(
            self.org.has_member(self.member),
            'The org should correctly report its members.'
        )

    def test_add_member(self):
        """Test adding a member to the organization."""
        new_member = muckrock.factories.UserFactory()
        self.org.add_member(new_member)
        eq_(
            self.org, new_member.profile.organization,
            'The new member should be added to the org.'
        )
        ok_(
            self.org.has_member(new_member),
            'The org should recognize the new member.'
        )

    def test_add_owner(self):
        """An owner should be able to add themself as a member of their own organization."""
        self.org.add_member(self.org.owner)
        eq_(
            self.org, self.org.owner.profile.organization,
            'The owner should be added as a member.'
        )
        ok_(
            self.org.has_member(self.owner),
            'The org should recognize the owner as a member.'
        )
        ok_(
            self.org.is_owned_by(self.owner),
            'The owner should also stay the owner.'
        )

    def test_remove_member(self):
        """Test removing a member from the organization."""
        self.org.remove_member(self.member)
        eq_(
            None, self.member.profile.organization,
            'The member should be removed from the org.'
        )
        ok_(
            not self.org.has_member(self.member),
            'The org should not recognize the ex-member.'
        )

    @nose.tools.raises(AttributeError)
    def test_add_member_without_seat(self):
        """An exception should be raised when trying to add a member without any available seat."""
        muckrock.factories.UserFactory(profile__organization=self.org)
        muckrock.factories.UserFactory(profile__organization=self.org)
        eq_(self.org.max_users, 3, 'The org should start with three seats.')
        eq_(self.org.members.count(), 3, 'The org should have 3 members.')
        # adding a new member should throw an error
        self.org.add_member(muckrock.factories.UserFactory())

    @nose.tools.raises(AttributeError)
    def test_add_other_org_member(self):
        """Cannot add a member of a different organization."""
        other_org = muckrock.factories.OrganizationFactory()
        member = muckrock.factories.UserFactory(profile__organization=other_org)
        self.org.add_member(member)

    @nose.tools.raises(AttributeError)
    def test_add_other_owner(self):
        """Cannot add an owner of a different organization."""
        other_org = muckrock.factories.OrganizationFactory()
        self.org.add_member(other_org.owner)

    @nose.tools.raises(AttributeError)
    def test_add_member_inactive(self):
        """Owners cannot add members when the org is inactive."""
        self.org.active = False
        self.org.save()
        ok_(not self.org.active)
        self.org.add_member(muckrock.factories.UserFactory())
