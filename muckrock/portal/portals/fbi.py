# -*- coding: utf-8 -*-
"""
Logic for interacting with FBI portals automatically
"""

# Django
from django.utils import timezone

# Standard Library
import os
import re

# Third Party
import requests

# MuckRock
from muckrock.communication.models import PortalCommunication
from muckrock.foia.models import FOIACommunication
from muckrock.portal.portals.automated import PortalAutoReceiveMixin
from muckrock.portal.portals.manual import ManualPortal
from muckrock.portal.tasks import portal_task

FBI_PORTAL_EMAIL = os.environ.get('FBI_PORTAL_EMAIL', '')


class FBIPortal(PortalAutoReceiveMixin, ManualPortal):
    """FBI eFOIPA Portal integration"""

    router = [
        (r'eFOIA Request Received', 'confirm_open'),
        (r'eFOIA files available', 'document_reply'),
    ]

    def get_new_password(self):
        """The FBI portal does not use a password"""
        return ''

    def confirm_open(self, comm):
        """Confirm receipt of request"""
        comm.foia.status = 'processed'
        comm.foia.save()
        PortalCommunication.objects.create(
            communication=comm,
            sent_datetime=timezone.now(),
            portal=self.portal,
            direction='incoming',
        )

    def document_reply(self, comm):
        """Process incoming documents"""
        p_file_available = re.compile(
            r'There are eFOIA files available for you to download'
        )
        match = p_file_available.search(comm.communication)
        if match:
            portal_task.delay(self.portal.pk, 'document_reply_task', [comm.pk])
        else:
            ManualPortal.receive_msg(
                self,
                comm,
                reason='Unexpected email format',
            )

    def document_reply_task(self, comm_pk):
        """Download the documents asynchornously"""
        comm = FOIACommunication.objects.get(pk=comm_pk)
        p_document_link = re.compile(r'\* \[(?P<name>[^\]]+)\]\((?P<url>.*)\)')
        for name, url in p_document_link.findall(comm.communication):
            reply = requests.get(url)
            if reply.status_code != 200:
                ManualPortal.receive_msg(
                    self,
                    comm,
                    reason='Error downloading file: {}'.format(name),
                )
                return
            comm.attach_file(
                content=reply.content,
                name=name,
                source=self.portal.name,
            )
        self._accept_comm(
            comm,
            'There are eFOIA files available for you to download.',
        )

    def send_msg(self, comm, **kwargs):
        """Send a message via email if it is not a new submission"""
        # need to update communications to ensure we have the correct count
        # for figuring out if this is a new or update message
        comm.foia.communications.update()
        category, _ = comm.foia.process_manual_send(**kwargs)

        if category in ('f', 'u'):
            # send to default email address if we do not have one on file or
            # if the last reply was from the portal email address
            if comm.foia.email is None or comm.foia.email.email == FBI_PORTAL_EMAIL:
                comm.foia.email = comm.foia.agency.get_emails('primary',
                                                              'to').first()
                comm.foia.save()
            if comm.foia.email and comm.foia.email.status == 'good':
                # do not send email to bad email addresses
                comm.foia.send_email(comm, **kwargs)
            else:
                super(FBIPortal, self).send_msg(comm, **kwargs)
        else:
            super(FBIPortal, self).send_msg(comm, **kwargs)
