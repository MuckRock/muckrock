"""
Custom pipeline steps for oAuth authentication
"""
# Standard Library
import logging

# MuckRock
from muckrock.accounts.models import Profile

logger = logging.getLogger(__name__)


def associate_by_uuid(backend, response, *args, user=None, **kwargs):
    """Associate current auth with a user with the same uuid in the DB."""
    # pylint: disable=unused-argument

    uuid = response.get("uuid")
    if uuid:
        try:
            profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            return None
        else:
            return {"user": profile.user, "is_new": False}
    else:
        return None


def save_profile(backend, user, response, *args, **kwargs):
    """Update the user's profile based on information from squarelet"""
    # pylint: disable=unused-argument
    if not hasattr(user, "profile"):
        user.profile = Profile.objects.create(user=user, uuid=response["uuid"])
        user.save()
    Profile.objects.squarelet_update_or_create(response["uuid"], response)


def save_session_data(strategy, request, response, *args, **kwargs):
    """Save some data in the session"""
    # session_state and id_token are used for universal logout functionality
    session_state = strategy.request_data().get("session_state")
    if session_state:
        request.session["session_state"] = session_state

    id_token = response.get("id_token")
    if id_token:
        request.session["id_token"] = id_token
