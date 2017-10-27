# -*- coding: utf-8 -*-
"""Logic for the different portal types"""

import string

from muckrock.task.models import PortalTask
from muckrock.utils import generate_key


class ManualPortal(object):
    """A fall-back type to manually handle portals we cannot automate yet"""

    @classmethod
    def send_msg(cls, comm, **kwargs):
        """Send a message via the portal"""
        category, _ = comm.foia.process_manual_send(**kwargs)
        PortalTask.objects.create(
                category=category,
                communication=comm,
                )

    @classmethod
    def receive_msg(cls, comm):
        """Receive a message from the portal"""
        PortalTask.objects.create(
                category='i',
                communication=comm,
                )

    @classmethod
    def get_new_password(cls):
        """Generate a random password to use with this portal"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return generate_key(12, chars=chars)
