"""
Tests for blocking a user from filing new requests
"""

# Django
from django.test import TestCase
from django.urls import reverse

# MuckRock
from muckrock.core.factories import UserFactory


class TestBlockedFromFilingProfile(TestCase):
    """The blocked from filing flag lives on the user's profile"""

    def test_default_not_blocked(self):
        """Users are able to file by default"""
        user = UserFactory()
        assert not user.profile.blocked_from_filing
        assert user.has_perm("foia.add_foiarequest")

    def test_blocked_loses_permission(self):
        """A blocked user may not add requests"""
        user = UserFactory(profile__blocked_from_filing=True)
        assert not user.has_perm("foia.add_foiarequest")


class TestBlockedFromFilingAdmin(TestCase):
    """Staff can find blocked users in the user admin"""

    def setUp(self):
        self.superuser = UserFactory(is_staff=True, is_superuser=True)
        self.blocked = UserFactory(profile__blocked_from_filing=True)
        self.unblocked = UserFactory()
        self.url = reverse("admin:auth_user_changelist")
        self.client.force_login(self.superuser)

    def test_filter_blocked(self):
        """Filtering on blocked shows only blocked users"""
        response = self.client.get(self.url, {"profile__blocked_from_filing__exact": 1})
        assert response.status_code == 200
        usernames = [user.username for user in response.context["cl"].result_list]
        assert usernames == [self.blocked.username]

    def test_filter_not_blocked(self):
        """Filtering on not blocked excludes blocked users"""
        response = self.client.get(self.url, {"profile__blocked_from_filing__exact": 0})
        assert response.status_code == 200
        usernames = [user.username for user in response.context["cl"].result_list]
        assert self.blocked.username not in usernames
        assert self.unblocked.username in usernames

    def test_no_filter(self):
        """Without the filter, both users are listed"""
        response = self.client.get(self.url)
        assert response.status_code == 200
        usernames = [user.username for user in response.context["cl"].result_list]
        assert self.blocked.username in usernames
        assert self.unblocked.username in usernames
