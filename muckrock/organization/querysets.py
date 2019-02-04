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
        required_fields = {'name', 'slug', 'update_on', 'plan', 'max_users'}
        missing = required_fields - (required_fields & set(data.keys()))
        if missing:
            raise ValueError('Missing required fields: {}'.format(missing))
        # rename update_on to date_update
        # convert date_update from string to date
        if data['update_on'] is not None:
            # XXX error handle
            data['date_update'] = datetime.strptime(
                data['update_on'], '%Y-%m-%d'
            ).date()
        else:
            data['date_update'] = data['update_on']

        organization, created = self.model.objects.get_or_create(uuid=uuid)
        organization.update_data(data)

        return organization, created
