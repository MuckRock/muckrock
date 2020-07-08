"""
Tests for the FOIA Composer
"""

# pylint: disable=invalid-name
# pylint: disable=protected-access

# Django
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

# Third Party
from nose.tools import assert_false, assert_true, eq_, ok_

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.factories import FOIAComposerFactory, FOIARequestFactory
from muckrock.foia.forms.composers import BaseComposerForm
from muckrock.foia.models import FOIAComposer
from muckrock.organization.factories import MembershipFactory, OrganizationFactory


class TestFOIAComposer(TestCase):
    """Test the foia composer"""

    # XXX
    def _test_return_requests(self):
        """Test return requests"""
        organization = OrganizationFactory(num_requests=100)
        composer = FOIAComposerFactory(
            status="submitted",
            num_org_requests=1,
            num_monthly_requests=2,
            num_reg_requests=3,
            user__profile__num_requests=5,
            user__profile__monthly_requests=10,
            user__profile__organization=organization,
        )
        composer._return_requests({"regular": 2, "monthly": 0, "org": 1})
        composer.user.profile.refresh_from_db()
        composer.user.profile.organization.refresh_from_db()
        eq_(composer.num_reg_requests, 1)
        eq_(composer.num_monthly_requests, 2)
        eq_(composer.num_org_requests, 0)
        eq_(composer.user.profile.num_requests, 7)
        eq_(composer.user.profile.monthly_requests, 10)
        eq_(composer.user.profile.organization.num_requests, 101)

    def _test_calc_return_requests(self):
        """Test calculating the return requests"""
        composer = FOIAComposerFactory(
            status="submitted",
            agencies=AgencyFactory.create_batch(6),
            num_org_requests=1,
            num_monthly_requests=2,
            num_reg_requests=3,
            user__profile__num_requests=5,
            user__profile__monthly_requests=10,
            user__profile__organization=OrganizationFactory(num_requests=100),
        )
        values = [
            (7, 4, 2, 1),
            (6, 3, 2, 1),
            (5, 3, 2, 0),
            (4, 3, 1, 0),
            (3, 3, 0, 0),
            (2, 2, 0, 0),
            (1, 1, 0, 0),
        ]
        for total, reg, monthly, org in values:
            eq_(
                composer._calc_return_requests(total),
                {"regular": reg, "monthly": monthly, "org": org},
            )


class TestFOIAComposerQueryset(TestCase):
    """Test the foia composer queryset"""

    def setUp(self):
        """Create users for each test"""
        self.staff = UserFactory(is_staff=True)
        self.user = UserFactory()
        self.anon = AnonymousUser()

    def test_get_viewable_public(self):
        """Test get viewable for a public composer"""

        FOIARequestFactory(composer__status="filed", embargo=False)

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_true(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_true(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_embargoed(self):
        """Test get viewable for an embargoed composer"""

        FOIARequestFactory(composer__status="filed", embargo=True)

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_partial_embargoed(self):
        """Test get viewable for a partially embargoed composer"""

        foia = FOIARequestFactory(composer__status="filed", embargo=True)
        FOIARequestFactory(composer=foia.composer, embargo=False)

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_true(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_true(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_draft(self):
        """Test get viewable for a draft composer"""

        FOIAComposerFactory(status="started")

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_owner(self):
        """Test get viewable for the composer owner"""

        FOIARequestFactory(
            composer__status="filed", embargo=True, composer__user=self.user
        )

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_true(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_read_collaborator(self):
        """Test get viewable for a read collaborator"""

        foia = FOIARequestFactory(composer__status="filed", embargo=True)
        foia.add_viewer(self.user)

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_true(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_edit_collaborator(self):
        """Test get viewable for an edit collaborator"""

        foia = FOIARequestFactory(composer__status="filed", embargo=True)
        foia.add_editor(self.user)

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_true(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_org_shared(self):
        """Test get viewable for an org shared composer"""

        org = OrganizationFactory()
        org_user1 = UserFactory(profile__org_share=True)
        org_user2 = UserFactory()
        MembershipFactory(user=org_user1, organization=org, active=False)
        MembershipFactory(user=org_user2, organization=org, active=False)

        FOIARequestFactory(
            composer__status="filed",
            embargo=True,
            composer__user=org_user1,
            composer__organization=org,
        )

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_true(FOIAComposer.objects.get_viewable(org_user2).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.anon).exists())

    def test_get_viewable_org_not_shared(self):
        """Test get viewable for an org not shared composer"""

        org = OrganizationFactory()
        org_user1 = UserFactory(profile__org_share=False)
        org_user2 = UserFactory()
        MembershipFactory(user=org_user1, organization=org, active=False)
        MembershipFactory(user=org_user2, organization=org, active=False)

        FOIARequestFactory(
            composer__status="filed",
            embargo=True,
            composer__user=org_user1,
            composer__organization=org,
        )

        assert_true(FOIAComposer.objects.get_viewable(self.staff).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.user).exists())
        assert_false(FOIAComposer.objects.get_viewable(org_user2).exists())
        assert_false(FOIAComposer.objects.get_viewable(self.anon).exists())


class TestFOIAComposerForm(TestCase):
    """Test FOIA composer form"""

    def test_multi_clone(self):
        """Test cloning a multirequest"""
        foia = FOIARequestFactory(composer__status="filed", embargo=False)
        FOIARequestFactory(composer=foia.composer)
        form = BaseComposerForm(
            {"action": "save", "parent": foia.composer.pk},
            user=foia.composer.user,
            request=None,
        )
        ok_(form.is_valid())
