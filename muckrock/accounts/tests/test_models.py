"""
Tests accounts models
"""

# Django
from django.test import TestCase

# Third Party
from nose.tools import assert_false, assert_true, eq_, ok_

# MuckRock
from muckrock.accounts.models import Notification, Profile
from muckrock.core.factories import (
    NotificationFactory,
    ProfileFactory,
    UserFactory,
)
from muckrock.core.utils import new_action
from muckrock.foia.factories import FOIARequestFactory
from muckrock.organization.factories import (
    FreeEntitlementFactory,
    MembershipFactory,
    OrganizationEntitlementFactory,
    ProfessionalEntitlementFactory,
)


class TestProfileUnit(TestCase):
    """Unit tests for profile model"""

    def setUp(self):
        self.profile = ProfileFactory()

    def test_unicode(self):
        """Test profile model's __unicode__ method"""
        expected = "%s's Profile" % unicode(self.profile.user).capitalize()
        eq_(unicode(self.profile), expected)

    def test_feature_level(self):
        """Test getting a users max feature level from their entitlements"""
        free = ProfileFactory(
            user__membership__organization__entitlement=FreeEntitlementFactory()
        )
        pro = ProfileFactory(
            user__membership__organization__entitlement=
            ProfessionalEntitlementFactory()
        )
        org = ProfileFactory(
            user__membership__organization__entitlement=
            OrganizationEntitlementFactory()
        )

        eq_(free.feature_level, 0)
        eq_(pro.feature_level, 1)
        eq_(org.feature_level, 2)

        MembershipFactory(
            user=free.user, organization__entitlement__name='Organization'
        )

        # refresh from db because feature level is cached
        free = Profile.objects.get(pk=free.pk)

        # if in free entitlement and org entitlement, take the larger one
        eq_(free.feature_level, 2)

    def test_is_advanced(self):
        """Test whether the users are marked as advanced."""
        pro = ProfileFactory(
            user__membership__organization__entitlement=
            ProfessionalEntitlementFactory()
        )
        org = ProfileFactory(
            user__membership__organization__entitlement=
            OrganizationEntitlementFactory()
        )
        free = ProfileFactory(
            user__membership__organization__entitlement=FreeEntitlementFactory()
        )

        assert_true(pro.is_advanced())
        assert_true(org.is_advanced())
        assert_false(free.is_advanced())


class TestNotifications(TestCase):
    """Notifications connect actions to users and contain a read state."""

    def setUp(self):
        self.user = UserFactory()
        self.action = new_action(self.user, 'acted')
        self.notification = NotificationFactory()

    def test_create_notification(self):
        """Create a notification with a user and an action."""
        notification = Notification.objects.create(
            user=self.user, action=self.action
        )
        ok_(notification, 'Notification object should create without error.')
        ok_(
            isinstance(notification, Notification),
            'Object should be a Notification.'
        )
        ok_(
            notification.read is not True,
            'Notification sould be unread by default.'
        )

    def test_mark_read(self):
        """Notifications should be markable as read if unread and unread if read."""
        self.notification.mark_read()
        ok_(
            self.notification.read is True,
            'Notification should be marked as read.'
        )
        self.notification.mark_unread()
        ok_(
            self.notification.read is not True,
            'Notification should be marked as unread.'
        )

    def test_for_user(self):
        """Notifications should be filterable by a single user."""
        user_notification = NotificationFactory(user=self.user)
        user_notifications = Notification.objects.for_user(self.user)
        ok_(
            user_notification in user_notifications,
            'A notification for the user should be in the set returned.'
        )
        ok_(
            self.notification not in user_notifications,
            'A notification for another user should not be in the set returned.'
        )

    def test_for_model(self):
        """Notifications should be filterable by a model type."""
        foia = FOIARequestFactory()
        _action = new_action(UserFactory(), 'submitted', target=foia)
        object_notification = NotificationFactory(
            user=self.user, action=_action
        )
        model_notifications = Notification.objects.for_model(foia)
        ok_(
            object_notification in model_notifications,
            'A notification for the model should be in the set returned.'
        )
        ok_(
            self.notification not in model_notifications,
            'A notification not including the model should not be in the set returned.'
        )

    def test_for_object(self):
        """Notifications should be filterable by a single object."""
        foia = FOIARequestFactory()
        _action = new_action(UserFactory(), 'submitted', target=foia)
        object_notification = NotificationFactory(
            user=self.user, action=_action
        )
        object_notifications = Notification.objects.for_object(foia)
        ok_(
            object_notification in object_notifications,
            'A notification for the object should be in the set returned.'
        )
        ok_(
            self.notification not in object_notifications,
            'A notification not including the object should not be in the set returned.'
        )

    def test_get_unread(self):
        """Notifications should be filterable by their unread status."""
        self.notification.mark_unread()
        ok_(
            self.notification in Notification.objects.get_unread(),
            'Unread notifications should be in the set returned.'
        )
        self.notification.mark_read()
        ok_(
            self.notification not in Notification.objects.get_unread(),
            'Read notifications should not be in the set returned.'
        )
