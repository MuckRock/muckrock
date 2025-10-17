# Django
from django.conf import settings
from django.contrib.auth.models import Group, User

# Standard Library
from datetime import date

# MuckRock
from muckrock.message.email import TemplateEmail


class PermissionsDigest(TemplateEmail):
    """A digest that provides an overview of who has what permissions"""

    html_template = "accounts/email/permissions.html"
    text_template = "accounts/email/permissions.txt"

    def __init__(self, **kwargs):
        kwargs["to"] = settings.PERMISSIONS_DIGEST_EMAILS
        kwargs["extra_context"] = self.get_context()
        kwargs["subject"] = f"{date.today()} MuckRock Permissions Digest"
        super().__init__(**kwargs)

    def get_context(self):
        return {
            "superusers": User.objects.filter(is_superuser=True),
            "staff": User.objects.filter(is_staff=True),
            "groups": Group.objects.prefetch_related("user_set"),
            "user_permissions": User.user_permissions.through.objects.select_related(
                "user",
                "permission",
            ),
        }
