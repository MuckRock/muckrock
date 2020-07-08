"""Custom querysets for organization app"""

# Django
from django.db import models, transaction

# Standard Library
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class OrganizationQuerySet(models.QuerySet):
    """Object manager for profiles"""

    def get_cache(self):
        """Return organizationsto cache for a user"""
        return self.order_by("-individual", "name").select_related("entitlement")

    @transaction.atomic
    def squarelet_update_or_create(self, uuid, data):
        """Update or create records based on data from squarelet"""
        required_fields = {"name", "slug", "entitlements", "max_users", "individual"}
        missing = required_fields - (required_fields & set(data.keys()))
        if missing:
            raise ValueError("Missing required fields: {}".format(missing))
        required_entitlement_fields = {
            "name",
            "slug",
            "description",
            "resources",
            "update_on",
        }
        # rename update_on to date_update
        # convert update_on from string to date
        for entitlement_data in data["entitlements"]:
            missing = required_entitlement_fields - (
                required_entitlement_fields & set(entitlement_data.keys())
            )
            if missing:
                raise ValueError(
                    "Missing required entitlement fields: {}".format(missing)
                )
            try:
                entitlement_data["date_update"] = datetime.strptime(
                    entitlement_data["update_on"], "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                # if there is no date, it will be None (TypeError)
                # if it is a malformed string we will get a ValueError
                # in either case just set to None
                entitlement_data["date_update"] = None
                logger.error(
                    "Bad `update_on` for organization %s: %s",
                    uuid,
                    entitlement_data["update_on"],
                )

        organization, created = self.model.objects.get_or_create(uuid=uuid)
        organization.update_data(data)

        return organization, created
