# Django
from django.db import models


class OrganizationStats(models.Model):
    """Staff-facing activity stats for an organization"""

    organization = models.OneToOneField(
        "organization.Organization",
        on_delete=models.CASCADE,
        related_name="stats",
        primary_key=True,
    )
    last_request_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"Stats for organization {self.organization_id}"
