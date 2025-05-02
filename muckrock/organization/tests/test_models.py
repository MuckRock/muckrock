"""
Tests the models of the organization application
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date

# Third Party
from nose.tools import assert_false, assert_raises, assert_true, eq_

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.organization.factories import (
    EntitlementFactory,
    FreeEntitlementFactory,
    MembershipFactory,
    OrganizationEntitlementFactory,
    OrganizationFactory,
)
from muckrock.organization.models import Organization


class TestOrganization(TestCase):
    """Tests for Organization methods"""

    def test_has_member(self):
        """Test has_member method"""
        org = OrganizationFactory()
        users = UserFactory.create_batch(2)
        MembershipFactory(user=users[0], organization=org)

        assert_true(org.has_member(users[0]))
        assert_false(org.has_member(users[1]))

    def test_has_admin(self):
        """Test has_admin method"""
        org = OrganizationFactory()
        users = UserFactory.create_batch(2)
        MembershipFactory(user=users[0], organization=org, admin=True)
        MembershipFactory(user=users[1], organization=org, admin=False)

        assert_true(org.has_admin(users[0]))
        assert_false(org.has_admin(users[1]))

    def test_make_requests(self):
        """Test Org make_requests method"""
        org = OrganizationFactory(monthly_requests=10, number_requests=10)

        request_count = org.make_requests(5)
        org.refresh_from_db()
        eq_(request_count, {"monthly": 5, "regular": 0})
        eq_(org.monthly_requests, 5)
        eq_(org.number_requests, 10)

        request_count = org.make_requests(10)
        org.refresh_from_db()
        eq_(request_count, {"monthly": 5, "regular": 5})
        eq_(org.monthly_requests, 0)
        eq_(org.number_requests, 5)

        request_count = org.make_requests(4)
        org.refresh_from_db()
        eq_(request_count, {"monthly": 0, "regular": 4})
        eq_(org.monthly_requests, 0)
        eq_(org.number_requests, 1)

        with assert_raises(InsufficientRequestsError):
            request_count = org.make_requests(2)
        org.refresh_from_db()
        eq_(org.monthly_requests, 0)
        eq_(org.number_requests, 1)

    def test_merge(self):

        users = UserFactory.create_batch(4)

        org = OrganizationFactory()
        MembershipFactory(user=users[0], organization=org)
        MembershipFactory(user=users[1], organization=org)
        dupe_org = OrganizationFactory()
        MembershipFactory(user=users[1], organization=dupe_org)
        MembershipFactory(user=users[2], organization=dupe_org)

        dupe_org.merge(org.uuid)

        # user 0, 1 and 2 in org
        for user_id in range(3):
            assert_true(org.has_member(users[user_id]))
        # user 3 not in org
        assert_false(org.has_member(users[3]))

        # no users in dupe_org
        eq_(dupe_org.users.count(), 0)

    def test_merge_fks(self):
        # Relations pointing to the Organization model
        eq_(
            len(
                [
                    f
                    for f in Organization._meta.get_fields()
                    if f.is_relation and f.auto_created
                ]
            ),
            2,
        )
        # Many to many relations defined on the Organization model
        eq_(
            len(
                [
                    f
                    for f in Organization._meta.get_fields()
                    if f.many_to_many and not f.auto_created
                ]
            ),
            1,
        )


def ent_json(entitlement, date_update):
    """Helper function for serializing entitlement data"""
    return {
        "name": entitlement.name,
        "slug": entitlement.slug,
        "description": entitlement.description,
        "resources": entitlement.resources,
        "date_update": date_update,
    }


class TestSquareletUpdateData(TestCase):
    """Test cases for updating organization data from squarelet"""

    def test_create_subscription(self):
        """Create a new subscription"""
        ent = OrganizationEntitlementFactory()
        organization = OrganizationFactory()
        organization.update_data(
            {
                "name": organization.name,
                "slug": organization.slug,
                "individual": False,
                "private": False,
                "entitlements": [ent_json(ent, date(2019, 2, 21))],
                "max_users": 5,
                "card": "",
            }
        )
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 50)
        eq_(organization.monthly_requests, 50)

    def test_cancel_subscription(self):
        """Cancel a subscription"""
        ent = FreeEntitlementFactory()
        organization = OrganizationFactory(
            entitlement=OrganizationEntitlementFactory(),
            date_update=date(2019, 2, 21),
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data(
            {
                "name": organization.name,
                "slug": organization.slug,
                "individual": False,
                "private": False,
                "entitlements": [ent_json(ent, None)],
                "max_users": 5,
                "card": "",
            }
        )
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 0)
        eq_(organization.monthly_requests, 0)

    def test_upgrade_subscription(self):
        """Upgrade a subscription"""
        ent = EntitlementFactory(
            name="Plus", resources=dict(minimum_users=5, base_requests=100)
        )
        organization = OrganizationFactory(
            entitlement=OrganizationEntitlementFactory(),
            date_update=date(2019, 2, 21),
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data(
            {
                "name": organization.name,
                "slug": organization.slug,
                "individual": False,
                "private": False,
                "entitlements": [ent_json(ent, date(2019, 2, 21))],
                "max_users": 5,
                "card": "",
            }
        )
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 100)
        eq_(organization.monthly_requests, 83)

    def test_downgrade_subscription(self):
        """Downgrade a subscription"""
        # Downgrades only happen at monthly restore
        ent = OrganizationEntitlementFactory()
        plus = EntitlementFactory(
            name="Plus", resources=dict(minimum_users=5, base_requests=100)
        )
        organization = OrganizationFactory(
            entitlement=plus,
            date_update=date(2019, 2, 21),
            requests_per_month=100,
            monthly_requests=83,
        )
        organization.update_data(
            {
                "name": organization.name,
                "slug": organization.slug,
                "individual": False,
                "private": False,
                "entitlements": [ent_json(ent, date(2019, 3, 21))],
                "max_users": 5,
                "card": "",
            }
        )
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 50)
        eq_(organization.monthly_requests, 50)

    def test_increase_max_users(self):
        """Increase max users"""
        ent = OrganizationEntitlementFactory()
        organization = OrganizationFactory(
            entitlement=ent,
            date_update=date(2019, 2, 21),
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data(
            {
                "name": organization.name,
                "slug": organization.slug,
                "individual": False,
                "private": False,
                "entitlements": [ent_json(ent, date(2019, 2, 21))],
                "max_users": 9,
                "card": "",
            }
        )
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 70)
        eq_(organization.monthly_requests, 53)

    def test_decrease_max_users(self):
        """Decrease max users"""
        ent = OrganizationEntitlementFactory()
        organization = OrganizationFactory(
            entitlement=ent,
            date_update=date(2019, 2, 21),
            requests_per_month=75,
            monthly_requests=33,
        )
        organization.update_data(
            {
                "name": organization.name,
                "slug": organization.slug,
                "individual": False,
                "private": False,
                "entitlements": [ent_json(ent, date(2019, 2, 21))],
                "max_users": 7,
                "card": "",
            }
        )
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 60)
        eq_(organization.monthly_requests, 33)

    def test_monthly_restore(self):
        """Monthly restore"""
        ent = OrganizationEntitlementFactory()
        organization = OrganizationFactory(
            entitlement=ent,
            date_update=date(2019, 2, 21),
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data(
            {
                "name": organization.name,
                "slug": organization.slug,
                "individual": False,
                "private": False,
                "entitlements": [ent_json(ent, date(2019, 3, 21))],
                "max_users": 5,
                "card": "",
            }
        )
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 50)
        eq_(organization.monthly_requests, 50)
