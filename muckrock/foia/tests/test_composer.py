"""
Tests for the FOIA Composer
"""

# Django
from django.test import TestCase

# Third Party
from nose.tools import eq_

# MuckRock
from muckrock.factories import OrganizationFactory
from muckrock.foia.factories import FOIAComposerFactory


class TestFOIAComposer(TestCase):
    """Test the foia composer"""

    def test_return_requests(self):
        """Test return requests"""
        organization = OrganizationFactory(num_requests=100)
        composer = FOIAComposerFactory(
            status='submitted',
            num_org_requests=1,
            num_monthly_requests=2,
            num_reg_requests=3,
            user__profile__num_requests=5,
            user__profile__monthly_requests=10,
            user__profile__organization=organization,
        )
        composer.return_requests({
            'regular': 2,
            'monthly': 0,
            'org': 1,
        })
        composer.user.profile.refresh_from_db()
        composer.user.profile.organization.refresh_from_db()
        eq_(composer.num_reg_requests, 1)
        eq_(composer.num_monthly_requests, 2)
        eq_(composer.num_org_requests, 0)
        eq_(composer.user.profile.num_requests, 7)
        eq_(composer.user.profile.monthly_requests, 10)
        eq_(composer.user.profile.organization.num_requests, 101)
