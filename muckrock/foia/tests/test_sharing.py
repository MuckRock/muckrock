"""
Tests sharing a FOIA request with other users
"""

# Django
from django.test import TestCase

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIARequestFactory
from muckrock.organization.factories import MembershipFactory, OrganizationFactory


class TestRequestSharing(TestCase):
    """Allow people to edit and view another user's request."""

    def setUp(self):
        self.foia = FOIARequestFactory()
        self.editor = UserFactory()
        self.creator = self.foia.user

    def test_add_editor(self):
        """Editors should be able to add editors to the request."""
        new_editor = self.editor
        self.foia.add_editor(new_editor)
        assert self.foia.has_editor(new_editor)

    def test_remove_editor(self):
        """Editors should be able to remove editors from the request."""
        editor_to_remove = self.editor
        # first we add the editor, otherwise we would have nothing to remove!
        self.foia.add_editor(editor_to_remove)
        assert self.foia.has_editor(editor_to_remove)
        # now we remove the editor we just added
        self.foia.remove_editor(editor_to_remove)
        assert not self.foia.has_editor(editor_to_remove)

    def test_editor_permission(self):
        """Editors should have the same abilities and permissions as creators."""
        new_editor = self.editor
        self.foia.add_editor(new_editor)
        assert self.foia.has_perm(new_editor, "change")

    def test_add_viewer(self):
        """Editors should be able to add viewers to the request."""
        new_viewer = UserFactory()
        self.foia.add_viewer(new_viewer)
        assert self.foia.has_viewer(new_viewer)

    def test_remove_viewer(self):
        """Editors should be able to remove viewers from the request."""
        viewer_to_remove = UserFactory()
        # first we add the viewer, otherwise we would have nothing to remove!
        self.foia.add_viewer(viewer_to_remove)
        assert self.foia.has_viewer(viewer_to_remove)
        # now we remove the viewer we just added
        self.foia.remove_viewer(viewer_to_remove)
        assert not self.foia.has_viewer(viewer_to_remove)

    def test_viewer_permission(self):
        """Viewers should be able to see the request if it is embargoed."""
        embargoed_foia = FOIARequestFactory(embargo_status="embargo")
        viewer = UserFactory()
        normie = UserFactory()
        embargoed_foia.add_viewer(viewer)
        assert embargoed_foia.has_perm(viewer, "view")
        assert not embargoed_foia.has_perm(normie, "view")

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        embargoed_foia = FOIARequestFactory(embargo_status="embargo")
        viewer = UserFactory()
        embargoed_foia.add_viewer(viewer)
        assert embargoed_foia.has_perm(viewer, "view")
        assert not embargoed_foia.has_perm(viewer, "change")
        embargoed_foia.promote_viewer(viewer)
        assert embargoed_foia.has_perm(viewer, "change")

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        embargoed_foia = FOIARequestFactory(embargo_status="embargo")
        editor = UserFactory()
        embargoed_foia.add_editor(editor)
        assert embargoed_foia.has_perm(editor, "view")
        assert embargoed_foia.has_perm(editor, "change")
        embargoed_foia.demote_editor(editor)
        assert not embargoed_foia.has_perm(editor, "change")

    def test_access_key(self):
        """Editors should be able to generate a secure access key to view an
        embargoed request."""
        embargoed_foia = FOIARequestFactory(embargo_status="embargo")
        access_key = embargoed_foia.generate_access_key()
        assert (
            access_key == embargoed_foia.access_key
        ), "The key in the URL should match the key saved to the request."
        embargoed_foia.generate_access_key()
        assert (
            access_key != embargoed_foia.access_key
        ), "After regenerating the link, the key should no longer match."

    def test_creator_access(self):
        """Creators should not be granted access as editors or viewers"""
        self.foia.add_editor(self.creator)
        assert not self.foia.has_editor(self.creator)
        self.foia.add_viewer(self.creator)
        assert not self.foia.has_viewer(self.creator)
        # but the creator should still be able to both view and edit!
        assert self.foia.has_perm(self.creator, "view")
        assert self.foia.has_perm(self.creator, "change")

    def test_org_share(self):
        """Test sharing with your organization"""
        org = OrganizationFactory()
        user = UserFactory()
        MembershipFactory(user=user, organization=org, active=False)
        self.foia.embargo_status = "embargo"
        self.foia.composer.organization = org
        # fellow org member cannot view it before sharing is turned on
        assert not self.foia.has_perm(user, "view")

        self.creator.profile.org_share = True
        # now org member can view it
        assert self.foia.has_perm(user, "view")
        # non-org member still cannot view it
        assert not self.foia.has_perm(self.editor, "view")
