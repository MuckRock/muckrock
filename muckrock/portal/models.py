# -*- coding: utf-8 -*-
"""Models for the portal application"""

# Django
from django.db import models

PORTAL_TYPES = [
    ('foiaonline', 'FOIAonline'),
    ('govqa', 'GovQA'),
    ('nextrequest', 'NextRequest'),
    ('foiaxpress', 'FOIAXpress'),
    ('fbi', 'FBI eFOIPA Portal'),
    ('other', 'Other'),
]


class Portal(models.Model):
    """An instance of an agency portal"""
    url = models.URLField(
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=255)
    type = models.CharField(
        choices=PORTAL_TYPES,
        max_length=11,
    )
    status = models.CharField(
        max_length=5,
        choices=(('good', 'Good'), ('error', 'Error')),
        default='good',
    )
    created_timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    @property
    def portal_type(self):
        """Get an instance of the portal type logic"""
        from muckrock.portal.portals import (
            ManualPortal,
            NextRequestPortal,
            FBIPortal,
        )
        # pylint: disable=access-member-before-definition
        # pylint: disable=attribute-defined-outside-init
        portal_classes = {
            'nextrequest': NextRequestPortal,
            'fbi': FBIPortal,
        }
        if hasattr(self, '_portal_type'):
            return self._portal_type
        else:
            portal_class = portal_classes.get(self.type, ManualPortal)
            self._portal_type = portal_class(self)
            return self._portal_type

    def send_msg(self, comm, **kwargs):
        """Send a message via this portal"""
        return self.portal_type.send_msg(comm, **kwargs)

    def receive_msg(self, comm):
        """Receive a message from this portal"""
        return self.portal_type.receive_msg(comm)

    def get_new_password(self):
        """Get a new password to use with this portal"""
        return self.portal_type.get_new_password()
