# Django
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

# Standard Library
import logging

# MuckRock
from muckrock.accounts.stats_api.models import UserStats

logger = logging.getLogger(__name__)


@receiver(
    post_save,
    sender=User,
    dispatch_uid="muckrock.accounts.signals.create_user_stats",
)
def create_user_stats(sender, instance, created, **kwargs):
    """Create a UserStats row when a new user is created.

    Users are also created via the Squarelet sync (library code), so post_save
    is the hook that catches all creation paths. Creates only, never updates.
    """
    # pylint: disable=unused-argument
    if created:
        UserStats.objects.get_or_create(user=instance)


@receiver(
    user_logged_in,
    dispatch_uid="muckrock.accounts.signals.log_agency_user_login",
)
def log_agency_user_login(sender, request, user, **kwargs):
    """Log every agency user login.

    Anyone CC'd on an agency email can follow its login link, so this is the
    record of who was signed in as the agency and from where.
    """
    # pylint: disable=unused-argument
    if not user.profile.is_agency_user:
        return
    if request is None:
        meta, path = {}, None
    else:
        meta, path = request.META, request.path
    logger.info(
        "Agency user login: user=%s (%s) agency=%s (%s) path=%s "
        "forwarded_for=%s remote_addr=%s user_agent=%s",
        user.username,
        user.pk,
        user.profile.agency.name,
        user.profile.agency_id,
        path,
        meta.get("HTTP_X_FORWARDED_FOR"),
        meta.get("REMOTE_ADDR"),
        meta.get("HTTP_USER_AGENT"),
    )
