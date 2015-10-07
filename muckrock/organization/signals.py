"""Signal handlers for organizations"""

from django.db.models.signals import post_save

import logging

from muckrock.organization.models import Organization

def make_owner_member(sender, **kwargs):
    """Ensure the owner of the organization is also a member"""
    # pylint: disable=unused-argument
    org = kwargs['instance']
    owner = org.owner
    owner.profile.organization = org
    owner.profile.save()

post_save.connect(make_owner_member, sender=Organization,
                  dispatch_uid='muckrock.organization.signals.make_owner_member')
