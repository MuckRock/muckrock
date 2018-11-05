"""
Custom pipeline steps for oAuth authentication
"""
# Standard Library
import logging

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.organization.models import Membership, Organization

logger = logging.getLogger(__name__)


def associate_by_uuid(backend, response, user=None, *args, **kwargs):
    """Associate current auth with a user with the same uuid in the DB."""
    # pylint: disable=unused-argument
    if user:
        return None

    uuid = response.get('uuid')
    if uuid:
        try:
            profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            return None
        else:
            return {'user': profile.user, 'is_new': False}


def save_profile(backend, user, response, *args, **kwargs):
    """Update the user's profile based on information from squarelet"""
    # pylint: disable=unused-argument
    if not hasattr(user, 'profile'):
        user.profile = Profile(
            user=user,
            acct_type='basic',
            uuid=response['uuid'],
        )

    old_email = user.email
    if 'email' in response:
        user.email = response['email']
        user.profile.email_confirmed = response['email_verified']
        if old_email != user.email:
            # if email has changed, update stripe customer and reset email failed flag
            # XXX put this in save / signal?
            customer = user.profile.customer()
            customer.email = user.email
            customer.save()
            user.profile.email_failed = False

    user.profile.full_name = response['name']
    if 'picture' in response:
        user.profile.avatar_url = response['picture']

    user.profile.save()
    user.save()


def link_organizations(backend, user, response, *args, **kwargs):
    """Link the users organizations"""
    # pylint: disable=unused-argument
    # XXX test
    new_organizations = set()
    for uuid, defaults in response['organizations'].iteritems():
        # the organization response has up to date information on all included orgs
        # XXX enforce name uniqueness?
        organization, _ = Organization.objects.update_or_create(
            uuid=uuid,
            defaults=defaults,
        )
        new_organizations.add(organization)

    current_organizations = set(user.organizations.all())
    add_organizations = new_organizations - current_organizations
    remove_organizations = current_organizations - new_organizations

    # user must have an active organization, if the current
    # active one is removed, we will activate another one
    active_organization = user.profile.organization
    active_removed = active_organization in remove_organizations

    # never remove the user's individual organization
    individual_organization = user.memberships.get(
        organization__individual=True
    )
    if individual_organization in remove_organizations:
        # XXX
        logger.error(
            'Trying to remove a user\'s individual organization: %s', user
        )
        remove_organizations.remove(individual_organization)

    user.memberships.bulk_create([
        Membership(user=user, organization=org, active=False)
        for org in add_organizations
    ])
    user.memberships.filter(organization__in=remove_organizations).delete()

    if active_removed:
        user.memberships.filter(organization__individual=True
                                ).update(active=True)


def save_session_data(strategy, request, response, *args, **kwargs):
    """Save some data in the session"""
    # pylint: disable=unused-argument
    # session_state and id_token are used for universal logout functionality
    session_state = strategy.request_data().get('session_state')
    if session_state:
        request.session['session_state'] = session_state

    id_token = response.get('id_token')
    if id_token:
        request.session['id_token'] = id_token
