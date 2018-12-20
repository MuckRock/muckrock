"""Custom querysets for organization app"""

# Django
from django.db import models, transaction

# MuckRock
from muckrock.organization.choices import Plan


class OrganizationQuerySet(models.QuerySet):
    """Object manager for profiles"""

    @transaction.atomic
    def squarelet_update_or_create(self, uuid, data):
        """Update or create records based on data from squarelet"""
        required_fields = {'name', 'slug'}
        missing = required_fields - (required_fields & set(data.keys()))
        if missing:
            raise ValueError('Missing required fields: {}'.format(missing))
        defaults = {
            'name': '',
            'slug': '',
            'private': False,
            'individual': False,
            'plan': Plan.free,
        }
        # remove extra data and set missing data to default values
        formatted_data = {
            k: data.get(k, defaults[k])
            for k in defaults.iterkeys()
        }
        # XXX instantiate resources if this is a non free plan!
        old_organization = self.model.objects.filter(uuid=uuid).first()
        organization, created = self.update_or_create(
            uuid=uuid, defaults=formatted_data
        )
