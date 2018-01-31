"""
This is the default portal logic for use with portals we have not automated yet.
It creates a task for all actions for a staff member to complete.  It is also
used as a fall back for automated portals when something goes wrong.
"""

# Standard Library
import string

# MuckRock
from muckrock.task.models import PortalTask
from muckrock.utils import generate_key


class ManualPortal(object):
    """A fall-back type to manually handle portals we cannot automate yet"""

    def __init__(self, portal):
        self.portal = portal

    def send_msg(self, comm, **kwargs):
        """Send a message via the portal"""
        category, _ = comm.foia.process_manual_send(**kwargs)
        PortalTask.objects.create(
            category=category,
            communication=comm,
            reason=kwargs.get('reason', ''),
        )

    def receive_msg(self, comm, **kwargs):
        """Receive a message from the portal"""
        PortalTask.objects.create(
            category='i',
            communication=comm,
            reason=kwargs.get('reason', ''),
        )

    def get_new_password(self):
        """Generate a random password to use with this portal"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return generate_key(12, chars=chars)
