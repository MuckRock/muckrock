# -*- coding: utf-8 -*-
"""Models for the portal application"""

from django.db import models

from muckrock.portal.portals import ManualPortal


PORTAL_TYPES = (
        ('foiaonline', 'FOIAonline'),
        ('govqa', 'GovQA'),
        ('nextrequest', 'NextRequest'),
        ('fbi', 'FBI eFOIPA Portal'),
        ('other', 'Other'),
        )


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

    def __unicode__(self):
        return self.name

    @property
    def portal_type(self):
        """Get an instance of the portal type logic"""
        # pylint: disable=access-member-before-definition
        # pylint: disable=attribute-defined-outside-init
        portal_classes = {}
        if hasattr(self, '_portal_type'):
            return self._portal_type
        else:
            self._portal_type = portal_classes.get(self.type, ManualPortal)
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
