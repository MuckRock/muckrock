"""Custom querysets for account app"""

# Django
from django.contrib.auth.models import User
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

        required_fields = {'preferred_username', 'email'}
        missing = required_fields - (required_fields & set(data.keys()))
        if missing:
            raise ValueError('Missing required fields: {}'.format(missing))
        old_user = User.objects.filter(profile__uuid=uuid).first()

        user = self._squarelet_update_or_create_user(uuid, data)
        # if they have changed their email address, reset email failed flag
        reset_email_failed = old_user and (old_user.email != user.email)

        profile = self._squarelet_update_or_create_profile(
            uuid, data, reset_email_failed
        )

        self._update_organizations(user, profile, data)

    def _squarelet_update_or_create_user(self, uuid, data):
        """Format user data and update or create the user"""
        user_map = {
            'preferred_username': 'username',
            'email': 'email',
        }
        user_defaults = {
            'preferred_username': '',
            'email': '',
        }
        user_data = {
            user_map[k]: data.get(k, user_defaults[k])
            for k in data.iterkeys()
        }
        user, _ = User.objects.update_or_create(
            profile__uuid=uuid, defaults=user_data
        )
        return user

    def _squarelet_update_or_create_profile(
        self, uuid, data, reset_email_failed
    ):
        """Format user data and update or create the user"""
        profile_map = {
            'name': 'full_name',
            'picture': 'avatar_url',
            'email_verified': 'email_confirmed',
        }
        profile_defaults = {
            'name': '',
            'picture': '',
            'emailed_verified': False,
        }
        if reset_email_failed:
            profile_defaults['email_failed'] = False
        profile_data = {
            profile_map[k]: data.get(k, profile_defaults[k])
            for k in data.iterkeys()
        }
        profile, _ = self.objects.update_or_create(
            uuid=uuid, defaults=profile_data
        )
        return profile

    def _update_organizations(self, user, profile, data):
        """Update the user's organizations"""
        current_organizations = set(user.organizations.all())
        new_memberships = []

        # process each organization
        for org_data in data.get('organizations', []):
            organization, _ = Organization.objects.squarelet_update_or_create(
                uuid=org_data['uuid'],
                data=org_data,
            )
            if organization in current_organizations:
                # remove organizations from our set as we see them
                # any that are left will need to be removed
                current_organizations.remove(organization)
            else:
                # if not currently a member, create the new membership
                new_memberships.append(
                    Membership(
                        user=user,
                        organization=organization,
                        active=False,
                        admin=org_data['admin'],
                    )
                )
        user.memberships.bulk_create(new_memberships)

        # user must have an active organization, if the current
        # active one is removed, we will activate the user's individual organization
        if profile.organization in current_organizations:
            user.memberships.filter(
                organization__individual=True,
            ).update(active=True)

        # never remove the user's individual organization
        individual_organization = user.memberships.get(
            organization__individual=True
        )
        if individual_organization in current_organizations:
            logger.error(
                'Trying to remove a user\'s individual organization: %s', user
            )
            current_organizations.remove(individual_organization)

        user.memberships.filter(organization__in=current_organizations).delete()
