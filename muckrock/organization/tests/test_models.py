"""
Tests the models of the organization application
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date

# Third Party
from nose.tools import eq_

# MuckRock
from muckrock.organization.factories import (
    FreePlanFactory,
    OrganizationFactory,
    OrganizationPlanFactory,
    PlanFactory,
    ProfessionalPlanFactory,
)


class TestSquareletUpdateData(TestCase):
    """Test cases for updating organization data from squarelet"""

    def test_create_subscription(self):
        """Create a new subscription"""
        OrganizationPlanFactory()
        organization = OrganizationFactory()
        organization.update_data({
            'name': organization.name,
            'slug': organization.slug,
            'individual': False,
            'private': False,
            'plan': 'organization',
            'date_update': date(2019, 2, 21),
            'max_users': 5,
            'card': '',
        })
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 50)
        eq_(organization.monthly_requests, 50)

    def test_cancel_subscription(self):
        """Cancel a subscription"""
        FreePlanFactory()
        organization = OrganizationFactory(
            plan=OrganizationPlanFactory(),
            date_update=date(2019, 2, 21),
            max_users=5,
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data({
            'name': organization.name,
            'slug': organization.slug,
            'individual': False,
            'private': False,
            'plan': 'free',
            'date_update': None,
            'max_users': 5,
            'card': '',
        })
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 0)
        eq_(organization.monthly_requests, 0)

    def test_upgrade_subscription(self):
        """Upgrade a subscription"""
        PlanFactory(
            name='Plus',
            minimum_users=5,
            base_requests=100,
        )
        organization = OrganizationFactory(
            plan=OrganizationPlanFactory(),
            date_update=date(2019, 2, 21),
            max_users=5,
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data({
            'name': organization.name,
            'slug': organization.slug,
            'individual': False,
            'private': False,
            'plan': 'plus',
            'date_update': date(2019, 2, 21),
            'max_users': 5,
            'card': '',
        })
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 100)
        eq_(organization.monthly_requests, 83)

    def test_downgrade_subscription(self):
        """Downgrade a subscription"""
        # Downgrades only happen at monthly restore
        OrganizationPlanFactory()
        plus = PlanFactory(
            name='Plus',
            minimum_users=5,
            base_requests=100,
        )
        organization = OrganizationFactory(
            plan=plus,
            date_update=date(2019, 2, 21),
            max_users=5,
            requests_per_month=100,
            monthly_requests=83,
        )
        organization.update_data({
            'name': organization.name,
            'slug': organization.slug,
            'individual': False,
            'private': False,
            'plan': 'organization',
            'date_update': date(2019, 3, 21),
            'max_users': 5,
            'card': '',
        })
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 50)
        eq_(organization.monthly_requests, 50)

    def test_increase_max_users(self):
        """Increase max users"""
        organization = OrganizationFactory(
            plan=OrganizationPlanFactory(),
            date_update=date(2019, 2, 21),
            max_users=5,
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data({
            'name': organization.name,
            'slug': organization.slug,
            'individual': False,
            'private': False,
            'plan': 'organization',
            'date_update': date(2019, 2, 21),
            'max_users': 9,
            'card': '',
        })
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 70)
        eq_(organization.monthly_requests, 53)

    def test_decrease_max_users(self):
        """Decrease max users"""
        organization = OrganizationFactory(
            plan=OrganizationPlanFactory(),
            date_update=date(2019, 2, 21),
            max_users=10,
            requests_per_month=75,
            monthly_requests=33,
        )
        organization.update_data({
            'name': organization.name,
            'slug': organization.slug,
            'individual': False,
            'private': False,
            'plan': 'organization',
            'date_update': date(2019, 2, 21),
            'max_users': 7,
            'card': '',
        })
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 60)
        eq_(organization.monthly_requests, 33)

    def test_monthly_restore(self):
        """Monthly restore"""
        organization = OrganizationFactory(
            plan=OrganizationPlanFactory(),
            date_update=date(2019, 2, 21),
            max_users=5,
            requests_per_month=50,
            monthly_requests=33,
        )
        organization.update_data({
            'name': organization.name,
            'slug': organization.slug,
            'individual': False,
            'private': False,
            'plan': 'organization',
            'date_update': date(2019, 3, 21),
            'max_users': 5,
            'card': '',
        })
        organization.refresh_from_db()
        eq_(organization.requests_per_month, 50)
        eq_(organization.monthly_requests, 50)
