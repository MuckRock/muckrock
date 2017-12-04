"""
Shared logic for handling automated portal processing
"""

from django.core.files.base import ContentFile
from django.db import transaction

from datetime import datetime
import re

from muckrock.communication.models import PortalCommunication
from muckrock.foia.models import FOIAFile
from muckrock.foia.tasks import upload_document_cloud, classify_status
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
        super(PortalAutoReceiveMixin, self).__init__(self, *args, **kwargs)

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

    def _attach_file(self, comm, name, content):
        """Helper method to attach a file to a communication"""
        with transaction.atomic():
            foia_file = FOIAFile.objects.create(
                    foia=comm.foia,
                    comm=comm,
                    title=name[:255],
                    date=datetime.now(),
                    source=self.portal.name,
                    access='private' if comm.foia.embargo else 'public',
                    )
            foia_file.ffile.save(name, ContentFile(content))
            transaction.on_commit(lambda f=foia_file:
                    upload_document_cloud.delay(f.pk, False))
        return foia_file

    def _accept_comm(self, comm):
        """Accept a communication onto the site"""
        comm.hidden = False
        comm.create_agency_notifications()
        comm.save()
        task = ResponseTask.objects.create(communication=comm)
        classify_status.apply_async(args=(task.pk,), countdown=30 * 60)
        PortalCommunication.objects.create(
                communication=comm,
                sent_datetime=datetime.now(),
                portal=self.portal,
                direction='incoming',
                )
