"""
Tests sharing a FOIA request with other users
"""

# Django
from django.test import TestCase

# Third Party
from nose.tools import assert_false, assert_true, ok_

# MuckRock
from muckrock.factories import OrganizationFactory, UserFactory
from muckrock.foia.factories import FOIARequestFactory


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
        assert_true(self.foia.has_editor(new_editor))

    def test_remove_editor(self):
        """Editors should be able to remove editors from the request."""
        editor_to_remove = self.editor
        # first we add the editor, otherwise we would have nothing to remove!
        self.foia.add_editor(editor_to_remove)
        assert_true(self.foia.has_editor(editor_to_remove))
        # now we remove the editor we just added
        self.foia.remove_editor(editor_to_remove)
        assert_false(self.foia.has_editor(editor_to_remove))

    def test_editor_permission(self):
        """Editors should have the same abilities and permissions as creators."""
        new_editor = self.editor
        self.foia.add_editor(new_editor)
        ok_(self.foia.has_perm(new_editor, 'change'))

    def test_add_viewer(self):
        """Editors should be able to add viewers to the request."""
        new_viewer = UserFactory()
        self.foia.add_viewer(new_viewer)
        ok_(self.foia.has_viewer(new_viewer))

    def test_remove_viewer(self):
        """Editors should be able to remove viewers from the request."""
        viewer_to_remove = UserFactory()
        # first we add the viewer, otherwise we would have nothing to remove!
        self.foia.add_viewer(viewer_to_remove)
        ok_(self.foia.has_viewer(viewer_to_remove))
        # now we remove the viewer we just added
        self.foia.remove_viewer(viewer_to_remove)
        assert_false(self.foia.has_viewer(viewer_to_remove))

    def test_viewer_permission(self):
        """Viewers should be able to see the request if it is embargoed."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        normie = UserFactory()
        embargoed_foia.add_viewer(viewer)
        assert_true(embargoed_foia.has_perm(viewer, 'view'))
        assert_false(embargoed_foia.has_perm(normie, 'view'))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        embargoed_foia.add_viewer(viewer)
        assert_true(embargoed_foia.has_perm(viewer, 'view'))
        assert_false(embargoed_foia.has_perm(viewer, 'change'))
        embargoed_foia.promote_viewer(viewer)
        assert_true(embargoed_foia.has_perm(viewer, 'change'))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        editor = UserFactory()
        embargoed_foia.add_editor(editor)
        assert_true(embargoed_foia.has_perm(editor, 'view'))
        assert_true(embargoed_foia.has_perm(editor, 'change'))
        embargoed_foia.demote_editor(editor)
        assert_false(embargoed_foia.has_perm(editor, 'change'))

    def test_access_key(self):
        """Editors should be able to generate a secure access key to view an embargoed request."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        access_key = embargoed_foia.generate_access_key()
        assert_true(
            access_key == embargoed_foia.access_key,
            'The key in the URL should match the key saved to the request.'
        )
        embargoed_foia.generate_access_key()
        assert_false(
            access_key == embargoed_foia.access_key,
            'After regenerating the link, the key should no longer match.'
        )

    def test_creator_access(self):
        """Creators should not be granted access as editors or viewers"""
        self.foia.add_editor(self.creator)
        assert_false(self.foia.has_editor(self.creator))
        self.foia.add_viewer(self.creator)
        assert_false(self.foia.has_viewer(self.creator))
        # but the creator should still be able to both view and edit!
        assert_true(self.foia.has_perm(self.creator, 'view'))
        assert_true(self.foia.has_perm(self.creator, 'change'))

    def test_org_share(self):
        """Test sharing with your organization"""
        org = OrganizationFactory()
        self.foia.embargo = True
        org.owner.profile.organization = org
        self.foia.user.profile.organization = org
        # fellow org member cannot view it before sharing is turned on
        assert_false(self.foia.has_perm(org.owner, 'view'))

        self.creator.profile.org_share = True
        # now org member can view it
        assert_true(self.foia.has_perm(org.owner, 'view'))
        # non-org member still cannot view it
        assert_false(self.foia.has_perm(self.editor, 'view'))
