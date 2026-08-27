# Django
from django.contrib.auth.models import User
from django.db import models


class UserStats(models.Model):
    """Staff-facing activity stats for a user"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="stats",
        primary_key=True,
    )
    last_request_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"Stats for user {self.user_id}"
