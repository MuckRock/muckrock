"""
Tests for the FOIA Composer
"""

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

    def test_return_requests(self):
        """Test return requests"""
        composer = FOIAComposerFactory(
            status="submitted", num_monthly_requests=2, num_reg_requests=3
        )
        composer.organization.number_requests = 100
        composer.organization.monthly_requests = 50
        composer.organization.save()
        composer._return_requests({"regular": 2, "monthly": 1})
        composer.refresh_from_db()
        eq_(composer.num_reg_requests, 1)
        eq_(composer.num_monthly_requests, 1)
        eq_(composer.organization.number_requests, 102)
        eq_(composer.organization.monthly_requests, 51)

    def test_calc_return_requests(self):
        """Test calculating the return requests"""
        composer = FOIAComposerFactory(
            status="submitted",
            agencies=AgencyFactory.create_batch(6),
            num_monthly_requests=2,
            num_reg_requests=3,
        )
        values = [(6, 4, 2), (5, 3, 2), (4, 3, 1), (3, 3, 0), (2, 2, 0), (1, 1, 0)]
        for total, reg, monthly in values:
            eq_(
                composer._calc_return_requests(total),
                {"regular": reg, "monthly": monthly},
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
            {"action": "save", "parent": foia.composer.pk, "tags": ""},
            user=foia.composer.user,
            request=None,
        )
        ok_(form.is_valid())
