"""Custom querysets for account app"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models, transaction

# Standard Library
import logging

# MuckRock
from muckrock.organization.models import Membership, Organization

logger = logging.getLogger(__name__)


class ProfileQuerySet(models.QuerySet):
    """Object manager for profiles"""

    @transaction.atomic
    def squarelet_update_or_create(self, uuid, data):
        """Update or create records based on data from squarelet"""

        required_fields = {"preferred_username", "organizations"}
        missing = required_fields - (required_fields & set(data.keys()))
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))

        user, created = self._squarelet_update_or_create_user(uuid, data)
        if created:
            user.set_unusable_password()
            user.save()

        profile = self._squarelet_update_or_create_profile(uuid, data, user)

        self._update_organizations(user, profile, data)

        return user, created

    def _squarelet_update_or_create_user(self, uuid, data):
        """Format user data and update or create the user"""
        user_map = {"preferred_username": "username", "email": "email"}
        user_defaults = {"preferred_username": "", "email": ""}
        user_data = {v: data.get(k, user_defaults[k]) for k, v in user_map.items()}
        if user_data["email"] is None:
            # the mail should only be null for agency users
            # on MuckRock that must be stored as a blank string
            user_data["email"] = ""
        return User.objects.update_or_create(profile__uuid=uuid, defaults=user_data)

    def _squarelet_update_or_create_profile(self, uuid, data, user):
        """Format user data and update or create the user"""
        profile_map = {
            "name": "full_name",
            "picture": "avatar_url",
            "email_failed": "email_failed",
            "email_verified": "email_confirmed",
            "use_autologin": "use_autologin",
            "agency": "agency",
            "bio": "profile",
        }
        profile_defaults = {
            "name": "",
            "picture": "",
            "email_failed": False,
            "email_verified": False,
            "use_autologin": True,
            "bio": "",
        }
        # if key is not present in profile_defaults, the default is to
        # leave it unchanged, do not include it in profile_data
        profile_data = {
            v: data.get(k, profile_defaults.get(k))
            for k, v in profile_map.items()
            if k in data or k in profile_defaults
        }
        profile_data["user"] = user
        profile, _ = self.update_or_create(uuid=uuid, defaults=profile_data)
        return profile

    def _update_organizations(self, user, profile, data):
        """Update the user's organizations"""
        current_organizations = set(user.organizations.all())
        new_memberships = []
        active = True

        # process each organization
        for org_data in data.get("organizations", []):
            organization, _ = Organization.objects.squarelet_update_or_create(
                uuid=org_data["uuid"], data=org_data
            )
            if organization in current_organizations:
                # remove organizations from our set as we see them
                # any that are left will need to be removed
                current_organizations.remove(organization)
                user.memberships.filter(organization=organization).update(
                    admin=org_data["admin"]
                )
            else:
                # if not currently a member, create the new membership
                # automatically activate new organizations (only first one)
                new_memberships.append(
                    Membership(
                        user=user,
                        organization=organization,
                        active=active,
                        admin=org_data["admin"],
                    )
                )
                active = False

        if new_memberships:
            # first new membership will be made active, de-activate current
            # active org first
            user.memberships.filter(active=True).update(active=False)
            user.memberships.bulk_create(new_memberships)

        # user must have an active organization, if the current
        # active one is removed, we will activate the user's individual organization
        if profile.organization in current_organizations:
            user.memberships.filter(organization__individual=True).update(active=True)

        # never remove the user's individual organization
        individual_organization = user.memberships.get(organization__individual=True)
        if individual_organization in current_organizations:
            logger.error("Trying to remove a user's individual organization: %s", user)
            current_organizations.remove(individual_organization)

        user.memberships.filter(organization__in=current_organizations).delete()

        # update cache after updating orgs
        cache.set(
            "sb:{}:user_org".format(user.username),
            profile.organization,
            settings.DEFAULT_CACHE_TIMEOUT,
        )
        cache.set(
            "sb:{}:user_orgs".format(user.username),
            user.organizations.get_cache(),
            settings.DEFAULT_CACHE_TIMEOUT,
        )
