"""
Tests sharing a FOIA request with other users
"""

from django.test import TestCase, RequestFactory

from nose.tools import eq_, ok_, assert_true, assert_false

from muckrock.factories import (
        FOIARequestFactory,
        UserFactory,
        OrganizationFactory,
        )
from muckrock.foia.views import Detail
from muckrock.test_utils import mock_middleware

# pylint: disable=no-self-use

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
        assert_true(access_key == embargoed_foia.access_key,
            'The key in the URL should match the key saved to the request.')
        embargoed_foia.generate_access_key()
        assert_false(access_key == embargoed_foia.access_key,
            'After regenerating the link, the key should no longer match.')

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


class TestRequestSharingViews(TestCase):
    """Tests access and implementation of view methods for sharing requests."""
    def setUp(self):
        self.factory = RequestFactory()
        self.foia = FOIARequestFactory()
        self.creator = self.foia.user
        self.editor = UserFactory()
        self.viewer = UserFactory()
        self.staff = UserFactory(is_staff=True)
        self.normie = UserFactory()
        self.foia.add_editor(self.editor)
        self.foia.add_viewer(self.viewer)
        self.foia.save()
        UserFactory(username='MuckrockStaff')

    def reset_access_key(self):
        """Simple helper to reset access key betweeen tests"""
        self.foia.access_key = None
        assert_false(self.foia.access_key)

    def test_access_key_allowed(self):
        """
        A POST request for a private share link should generate and return an access key.
        Editors and staff should be allowed to do this.
        """
        self.reset_access_key()
        data = {'action': 'generate_key'}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        # editors should be able to generate the key
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_true(self.foia.access_key)
        # staff should be able to generate the key
        self.reset_access_key()
        request.user = self.staff
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_true(self.foia.access_key)

    def test_access_key_not_allowed(self):
        """Visitors and normies should not be allowed to generate an access key."""
        self.reset_access_key()
        data = {'action': 'generate_key'}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        # viewers should not be able to generate the key
        request.user = self.viewer
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_false(self.foia.access_key)
        # normies should not be able to generate the key
        self.reset_access_key()
        request.user = self.normie
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_false(self.foia.access_key)

    def test_grant_edit_access(self):
        """Editors should be able to add editors."""
        user1 = UserFactory()
        user2 = UserFactory()
        edit_data = {
            'action': 'grant_access',
            'users': [user1.pk, user2.pk],
            'access': 'edit'
        }
        edit_request = self.factory.post(self.foia.get_absolute_url(), edit_data)
        edit_request = mock_middleware(edit_request)
        edit_request.user = self.editor
        edit_response = Detail.as_view()(
            edit_request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        eq_(edit_response.status_code, 302)
        assert_true(self.foia.has_editor(user1) and self.foia.has_editor(user2))

    def test_grant_view_access(self):
        """Editors should be able to add viewers."""
        user1 = UserFactory()
        user2 = UserFactory()
        view_data = {
            'action': 'grant_access',
            'users': [user1.pk, user2.pk],
            'access': 'view'
        }
        view_request = self.factory.post(self.foia.get_absolute_url(), view_data)
        view_request = mock_middleware(view_request)
        view_request.user = self.editor
        view_response = Detail.as_view()(
            view_request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        eq_(view_response.status_code, 302)
        assert_true(self.foia.has_viewer(user1) and self.foia.has_viewer(user2))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        user = UserFactory()
        self.foia.add_editor(user)
        assert_true(self.foia.has_editor(user))
        data = {
            'action': 'demote',
            'user': user.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_editor(user))
        assert_true(self.foia.has_viewer(user))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        user = UserFactory()
        self.foia.add_viewer(user)
        assert_true(self.foia.has_viewer(user))
        data = {
            'action': 'promote',
            'user': user.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_viewer(user))
        assert_true(self.foia.has_editor(user))

    def test_revoke_edit_access(self):
        """Editors should be able to revoke access from an editor."""
        an_editor = UserFactory()
        self.foia.add_editor(an_editor)
        data = {
            'action': 'revoke_access',
            'user': an_editor.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_editor(an_editor))

    def test_revoke_view_access(self):
        """Editors should be able to revoke access from a viewer."""
        a_viewer = UserFactory()
        self.foia.add_viewer(a_viewer)
        data = {
            'action': 'revoke_access',
            'user': a_viewer.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        eq_(response.status_code, 302)
        assert_false(self.foia.has_viewer(a_viewer))
