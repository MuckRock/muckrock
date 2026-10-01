# Django
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# MuckRock
from muckrock.accounts.stats_api.models import UserStats


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
