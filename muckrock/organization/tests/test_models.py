"""
Tests the models of the organization application
"""

# Django
from django.contrib.auth.models import User
from django.test import TestCase

# Standard Library
from datetime import date

# Third Party
import pytest

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.organization.factories import (
    EntitlementFactory,
    FreeEntitlementFactory,
    MembershipFactory,
    OrganizationEntitlementFactory,
    OrganizationFactory,
    ProfessionalEntitlementFactory,
)
from muckrock.organization.models import Organization


class TestOrganization(TestCase):
    """Tests for Organization methods"""

    def test_has_member(self):
        """Test has_member method"""
        org = OrganizationFactory()
        users = UserFactory.create_batch(2)
        MembershipFactory(user=users[0], organization=org)

        assert org.has_member(users[0])
        assert not org.has_member(users[1])

    def test_has_admin(self):
        """Test has_admin method"""
        org = OrganizationFactory()
        users = UserFactory.create_batch(2)
        MembershipFactory(user=users[0], organization=org, admin=True)
        MembershipFactory(user=users[1], organization=org, admin=False)

        assert org.has_admin(users[0])
        assert not org.has_admin(users[1])

    def test_make_requests(self):
        """Test Org make_requests method"""
        org = OrganizationFactory(monthly_requests=10, number_requests=10)

        request_count = org.make_requests(5)
        org.refresh_from_db()
        assert request_count == {"monthly": 5, "regular": 0}
        assert org.monthly_requests == 5
        assert org.number_requests == 10

        request_count = org.make_requests(10)
        org.refresh_from_db()
        assert request_count == {"monthly": 5, "regular": 5}
        assert org.monthly_requests == 0
        assert org.number_requests == 5

        request_count = org.make_requests(4)
        org.refresh_from_db()
        assert request_count == {"monthly": 0, "regular": 4}
        assert org.monthly_requests == 0
        assert org.number_requests == 1

        with pytest.raises(InsufficientRequestsError):
            request_count = org.make_requests(2)
        org.refresh_from_db()
        assert org.monthly_requests == 0
        assert org.number_requests == 1

    def test_merge(self):

        users = UserFactory.create_batch(4)

        org = OrganizationFactory()
        MembershipFactory(user=users[0], organization=org, active=True)
        MembershipFactory(user=users[1], organization=org, active=False)
        dupe_org = OrganizationFactory()
        MembershipFactory(user=users[1], organization=dupe_org, active=True)
        MembershipFactory(user=users[2], organization=dupe_org, active=True)
        # set active orgs
        users[0].profile.organization = org
        users[1].profile.organization = dupe_org
        users[2].profile.organization = dupe_org

        dupe_org.merge(org.uuid)

        # user 0, 1 and 2 in org
        for user_id in range(3):
            assert org.has_member(users[user_id])
        # user 3 not in org
        assert not org.has_member(users[3])

        # all users have exactly one active org
        for user in User.objects.all():
            assert user.profile.organization

        # no users in dupe_org
        assert dupe_org.users.count() == 0

    def test_merge_fks(self):
        # Relations pointing to the Organization model
        assert (
            len(
                [
                    f
                    for f in Organization._meta.get_fields()
                    if f.is_relation and f.auto_created
                ]
            )
            == 4
        )
        # Many to many relations defined on the Organization model
        assert (
            len(
                [
                    f
                    for f in Organization._meta.get_fields()
                    if f.many_to_many and not f.auto_created
                ]
            )
            == 2
        )


def ent_json(entitlement, date_update, quantity=1):
    """Helper function for serializing entitlement data"""
    return {
        "name": entitlement.name,
        "slug": entitlement.slug,
        "description": entitlement.description,
        "resources": entitlement.resources,
        "date_update": date_update,
        "quantity": quantity,
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
                "card": "",
            }
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 50
        assert organization.monthly_requests == 50

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
                "card": "",
            }
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 0
        assert organization.monthly_requests == 0

    def test_upgrade_subscription(self):
        """Upgrade a subscription"""
        ent = EntitlementFactory(
            name="Plus",
            resources={"minimum_users": 5, "base_requests": 100},
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
                "card": "",
            }
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 100
        assert organization.monthly_requests == 83

    def test_downgrade_subscription(self):
        """Downgrade a subscription"""
        # Downgrades only happen at monthly restore
        ent = OrganizationEntitlementFactory()
        plus = EntitlementFactory(
            name="Plus",
            resources={"minimum_users": 5, "base_requests": 100},
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
                "card": "",
            }
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 50
        assert organization.monthly_requests == 50

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
                "entitlements": [
                    ent_json(ent, date(2019, 2, 21), quantity=9)
                ],
                "card": "",
            }
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 70
        assert organization.monthly_requests == 53

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
                "entitlements": [
                    ent_json(ent, date(2019, 2, 21), quantity=7)
                ],
                "card": "",
            }
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 60
        assert organization.monthly_requests == 33

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
                "card": "",
            }
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 50
        assert organization.monthly_requests == 50


class TestSquareletUpdateDataMultiEntitlement(TestCase):
    """Test cases for update_data with multiple entitlements"""

    def _org_data(self, organization, entitlements):
        return {
            "name": organization.name,
            "slug": organization.slug,
            "individual": False,
            "private": False,
            "entitlements": entitlements,
            "card": "",
        }

    def test_two_paid_entitlements_sums_requests(self):
        """Two paid entitlements: requests_per_month = sum of both"""
        ent1 = ProfessionalEntitlementFactory()
        ent2 = OrganizationEntitlementFactory()
        organization = OrganizationFactory()
        date_update = date(2024, 3, 1)

        organization.update_data(
            self._org_data(
                organization,
                [
                    ent_json(ent1, date_update, quantity=1),
                    ent_json(ent2, date_update, quantity=5),
                ],
            )
        )
        organization.refresh_from_db()
        # Professional: 20 + max(0, 1-1)*0 = 20
        # Organization: 50 + max(0, 5-5)*5 = 50
        assert organization.requests_per_month == 70
        assert organization.monthly_requests == 70

    def test_paid_and_grant_entitlement_sums_requests(self):
        """Paid entitlement + grant entitlement: both contribute to total"""
        paid = OrganizationEntitlementFactory()
        grant = EntitlementFactory(
            name="Grant",
            resources={"minimum_users": 1, "base_requests": 10, "feature_level": 0},
        )
        organization = OrganizationFactory()
        date_update = date(2024, 3, 1)

        organization.update_data(
            self._org_data(
                organization,
                [
                    ent_json(paid, date_update, quantity=5),
                    ent_json(grant, date_update, quantity=1),
                ],
            )
        )
        organization.refresh_from_db()
        # Organization: 50 + max(0, 5-5)*5 = 50, Grant: 10 + max(0, 1-1)*0 = 10
        assert organization.requests_per_month == 60
        assert organization.monthly_requests == 60

    def test_primary_entitlement_is_highest_feature_level(self):
        """org.entitlement FK points to entitlement with highest feature_level"""
        low = ProfessionalEntitlementFactory()  # feature_level=1
        high = OrganizationEntitlementFactory()  # feature_level=2
        organization = OrganizationFactory()
        date_update = date(2024, 3, 1)

        organization.update_data(
            self._org_data(
                organization,
                [
                    ent_json(low, date_update, quantity=1),
                    ent_json(high, date_update, quantity=5),
                ],
            )
        )
        organization.refresh_from_db()
        assert organization.entitlement.slug == high.slug

    def test_equal_feature_level_tie_breaks_to_first(self):
        """Equal feature_level: first entitlement in list wins the FK"""
        ent1 = EntitlementFactory(
            name="GrantA",
            resources={"base_requests": 10, "feature_level": 1},
        )
        ent2 = EntitlementFactory(
            name="GrantB",
            resources={"base_requests": 20, "feature_level": 1},
        )
        organization = OrganizationFactory()
        date_update = date(2024, 3, 1)

        organization.update_data(
            self._org_data(
                organization,
                [
                    ent_json(ent1, date_update, quantity=1),
                    ent_json(ent2, date_update, quantity=1),
                ],
            )
        )
        organization.refresh_from_db()
        assert organization.entitlement.slug == ent1.slug
        assert organization.requests_per_month == 30

    def test_quantity_below_minimum_does_not_reduce_base(self):
        """quantity < minimum_users: base requests are not reduced"""
        ent = OrganizationEntitlementFactory()  # min=5, base=50, per_user=5
        organization = OrganizationFactory()

        organization.update_data(
            self._org_data(organization, [ent_json(ent, date(2024, 3, 1), quantity=2)])
        )
        organization.refresh_from_db()
        # max(0, 2-5) = 0, so just base=50
        assert organization.requests_per_month == 50

    def test_quantity_above_minimum_adds_per_user_requests(self):
        """quantity > minimum_users: extra quantity adds per-user requests"""
        ent = OrganizationEntitlementFactory()  # min=5, base=50, per_user=5
        organization = OrganizationFactory()

        organization.update_data(
            self._org_data(organization, [ent_json(ent, date(2024, 3, 1), quantity=8)])
        )
        organization.refresh_from_db()
        # 50 + max(0, 8-5)*5 = 50 + 15 = 65
        assert organization.requests_per_month == 65

    def test_multi_entitlement_monthly_restore(self):
        """Monthly restore resets monthly_requests to sum of all entitlements"""
        ent1 = ProfessionalEntitlementFactory()
        ent2 = OrganizationEntitlementFactory()
        organization = OrganizationFactory(
            entitlement=ent2,
            date_update=date(2024, 2, 1),
            requests_per_month=70,
            monthly_requests=20,
        )

        organization.update_data(
            self._org_data(
                organization,
                [
                    ent_json(ent1, date(2024, 3, 1), quantity=1),
                    ent_json(ent2, date(2024, 3, 1), quantity=5),
                ],
            )
        )
        organization.refresh_from_db()
        assert organization.requests_per_month == 70
        assert organization.monthly_requests == 70


class TestOrganizationCollective(TestCase):
    """Tests for Organization collective resource sharing"""

    def test_make_requests_with_parent(self):
        """Test making requests using parent's resources when own resources exhausted"""
        parent = OrganizationFactory(
            monthly_requests=20,
            number_requests=10,
            share_resources=True,
        )
        child = OrganizationFactory(
            monthly_requests=5,
            number_requests=3,
            parent=parent,
        )

        # Use child's own resources first
        request_count = child.make_requests(6)
        child.refresh_from_db()
        parent.refresh_from_db()
        assert request_count == {"monthly": 5, "regular": 1}
        assert child.monthly_requests == 0
        assert child.number_requests == 2
        assert parent.monthly_requests == 20  # Parent untouched
        assert parent.number_requests == 10

        # Use remaining child resources + parent resources
        request_count = child.make_requests(15)
        child.refresh_from_db()
        parent.refresh_from_db()
        assert request_count == {"monthly": 13, "regular": 2}
        assert child.monthly_requests == 0
        assert child.number_requests == 0
        assert parent.monthly_requests == 7  # Parent used
        assert parent.number_requests == 10

    def test_make_requests_parent_no_sharing(self):
        """Test that resources are not shared when parent.share_resources=False"""
        parent = OrganizationFactory(
            monthly_requests=20,
            number_requests=10,
            share_resources=False,
        )
        child = OrganizationFactory(
            monthly_requests=5,
            number_requests=0,
            parent=parent,
        )

        # Can only use child's own resources
        request_count = child.make_requests(5)
        child.refresh_from_db()
        parent.refresh_from_db()
        assert request_count == {"monthly": 5, "regular": 0}
        assert child.monthly_requests == 0
        assert parent.monthly_requests == 20  # Parent untouched
        assert parent.number_requests == 10

        # Cannot use parent's resources
        with pytest.raises(InsufficientRequestsError):
            child.make_requests(1)

    def test_make_requests_with_groups(self):
        """Test making requests using group's resources"""
        group = OrganizationFactory(
            monthly_requests=30,
            number_requests=20,
            share_resources=True,
        )
        member = OrganizationFactory(
            monthly_requests=2,
            number_requests=1,
        )
        group.members.add(member)

        # Use member's own resources + group resources
        request_count = member.make_requests(10)
        member.refresh_from_db()
        group.refresh_from_db()
        assert request_count == {"monthly": 9, "regular": 1}
        assert member.monthly_requests == 0
        assert member.number_requests == 0
        assert group.monthly_requests == 23
        assert group.number_requests == 20

    def test_make_requests_with_multiple_groups(self):
        """Test making requests from multiple groups"""
        group1 = OrganizationFactory(
            monthly_requests=10,
            number_requests=5,
            share_resources=True,
        )
        group2 = OrganizationFactory(
            monthly_requests=15,
            number_requests=10,
            share_resources=True,
        )
        member = OrganizationFactory(
            monthly_requests=0,
            number_requests=0,
        )
        group1.members.add(member)
        group2.members.add(member)

        # Use resources from both groups (arbitrary order)
        member.make_requests(20)
        member.refresh_from_db()
        group1.refresh_from_db()
        group2.refresh_from_db()

        # Total resources used should be 20
        total_used = (
            (10 - group1.monthly_requests)
            + (5 - group1.number_requests)
            + (15 - group2.monthly_requests)
            + (10 - group2.number_requests)
        )
        assert total_used == 20

    def test_make_requests_parent_and_groups(self):
        """Test making requests with both parent and groups"""
        parent = OrganizationFactory(
            monthly_requests=15,
            number_requests=10,
            share_resources=True,
        )
        group = OrganizationFactory(
            monthly_requests=20,
            number_requests=15,
            share_resources=True,
        )
        org = OrganizationFactory(
            monthly_requests=5,
            number_requests=3,
            parent=parent,
        )
        group.members.add(org)

        # Use own, then parent, then group resources
        org.make_requests(40)
        org.refresh_from_db()
        parent.refresh_from_db()
        group.refresh_from_db()

        assert org.monthly_requests == 0
        assert org.number_requests == 0
        # Parent should be depleted
        assert parent.monthly_requests == 0
        assert parent.number_requests == 0
        # Group should have been used
        assert (group.monthly_requests + group.number_requests) < (20 + 15)

    def test_get_total_number_requests_own_only(self):
        """Test get_total_number_requests with no parent or groups"""
        org = OrganizationFactory(number_requests=10)
        assert org.get_total_number_requests() == 10

    def test_get_total_number_requests_with_parent(self):
        """Test get_total_number_requests including parent"""
        parent = OrganizationFactory(
            number_requests=20,
            share_resources=True,
        )
        child = OrganizationFactory(
            number_requests=5,
            parent=parent,
        )
        assert child.get_total_number_requests() == 25

    def test_get_total_number_requests_parent_no_sharing(self):
        """Test get_total_number_requests when parent doesn't share"""
        parent = OrganizationFactory(
            number_requests=20,
            share_resources=False,
        )
        child = OrganizationFactory(
            number_requests=5,
            parent=parent,
        )
        assert child.get_total_number_requests() == 5

    def test_get_total_number_requests_with_groups(self):
        """Test get_total_number_requests including groups"""
        group1 = OrganizationFactory(
            number_requests=15,
            share_resources=True,
        )
        group2 = OrganizationFactory(
            number_requests=10,
            share_resources=True,
        )
        member = OrganizationFactory(number_requests=5)
        group1.members.add(member)
        group2.members.add(member)

        assert member.get_total_number_requests() == 30  # 5 + 15 + 10

    def test_get_total_monthly_requests_own_only(self):
        """Test get_total_monthly_requests with no parent or groups"""
        org = OrganizationFactory(monthly_requests=20)
        assert org.get_total_monthly_requests() == 20

    def test_get_total_monthly_requests_with_parent(self):
        """Test get_total_monthly_requests including parent"""
        parent = OrganizationFactory(
            monthly_requests=50,
            share_resources=True,
        )
        child = OrganizationFactory(
            monthly_requests=10,
            parent=parent,
        )
        assert child.get_total_monthly_requests() == 60

    def test_get_total_monthly_requests_with_groups(self):
        """Test get_total_monthly_requests including groups"""
        group = OrganizationFactory(
            monthly_requests=30,
            share_resources=True,
        )
        member = OrganizationFactory(monthly_requests=5)
        group.members.add(member)

        assert member.get_total_monthly_requests() == 35

    def test_insufficient_requests_with_parent(self):
        """Test InsufficientRequestsError even with parent resources"""
        parent = OrganizationFactory(
            monthly_requests=5,
            number_requests=3,
            share_resources=True,
        )
        child = OrganizationFactory(
            monthly_requests=2,
            number_requests=1,
            parent=parent,
        )

        # Total available is 11 (2+1 from child, 5+3 from parent)
        with pytest.raises(InsufficientRequestsError):
            child.make_requests(12)

        # Verify nothing was deducted due to transaction rollback
        child.refresh_from_db()
        parent.refresh_from_db()
        assert child.monthly_requests == 2
        assert child.number_requests == 1
        assert parent.monthly_requests == 5
        assert parent.number_requests == 3
