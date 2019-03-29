"""Custom querysets for organization app"""

# Django
from django.db import models, transaction

# Standard Library
from datetime import datetime


class OrganizationQuerySet(models.QuerySet):
    """Object manager for profiles"""

    @transaction.atomic
    def squarelet_update_or_create(self, uuid, data):
        """Update or create records based on data from squarelet"""
        required_fields = {
            'name',
            'slug',
            'update_on',
            'plan',
            'max_users',
            'individual',
        }
        missing = required_fields - (required_fields & set(data.keys()))
        if missing:
            raise ValueError('Missing required fields: {}'.format(missing))
        # rename update_on to date_update
        # convert date_update from string to date
        try:
            data['date_update'] = datetime.strptime(
                data['update_on'], '%Y-%m-%d'
            ).date()
        except (ValueError, TypeError):
            # if there is no date, it will be None (TypeError)
            # if it is a malformed string we will get a ValueError
            # in either case just set to None
            data['date_update'] = None

        organization, created = self.model.objects.get_or_create(uuid=uuid)
        organization.update_data(data)

        return organization, created
