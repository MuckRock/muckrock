# Django
from django.db.models.signals import post_save
from django.dispatch import receiver

# MuckRock
from muckrock.organization.models import Organization
from muckrock.organization.stats_api.models import OrganizationStats


@receiver(
    post_save,
    sender=Organization,
    dispatch_uid="muckrock.organization.signals.create_organization_stats",
)
def create_organization_stats(sender, instance, created, **kwargs):
    """Create an OrganizationStats row for new collective orgs.

    Skips individual orgs, matching the org stats endpoint and the backfill.
    """
    # pylint: disable=unused-argument
    if created and not instance.individual:
        OrganizationStats.objects.get_or_create(organization=instance)
