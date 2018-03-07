"""
Shared logic for handling automated portal processing
"""

# Django
from django.utils import timezone

# Standard Library
import re

# MuckRock
from muckrock.communication.models import PortalCommunication
from muckrock.foia.tasks import classify_status
from muckrock.task.models import ResponseTask


class PortalAutoReceiveMixin(object):
    """
    A mixin for handling receiving email messages and routing them to handlers
    based on the subject email
    """

    error_msg = 'Did not know how to handle'

    def __init__(self, *args, **kwargs):
        """Initialize the router"""
        self._router = [(re.compile(pattern), getattr(self, method))
                        for pattern, method in self.router]
        super(PortalAutoReceiveMixin, self).__init__(*args, **kwargs)

    def receive_msg(self, comm, **kwargs):
        """Route incoming messages"""
        # pylint: disable=unused-argument

        for pattern, handler in self._router:
            match = pattern.search(comm.subject)
            if match:
                handler(comm, **match.groupdict())
                break
        else:
            super(PortalAutoReceiveMixin, self).receive_msg(
                comm,
                reason=self.error_msg,
            )

    def _accept_comm(self, comm, text):
        """Accept a communication onto the site"""
        comm.communication = text
        comm.hidden = False
        comm.create_agency_notifications()
        comm.save()
        task = ResponseTask.objects.create(communication=comm)
        classify_status.apply_async(args=(task.pk,), countdown=30 * 60)
        PortalCommunication.objects.create(
            communication=comm,
            sent_datetime=timezone.now(),
            portal=self.portal,
            direction='incoming',
        )
