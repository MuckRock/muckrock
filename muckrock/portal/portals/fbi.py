# -*- coding: utf-8 -*-
"""
Logic for interacting with FBI portals automatically
"""

from datetime import datetime
import re
import requests

from muckrock.communication.models import PortalCommunication
from muckrock.foia.models import FOIACommunication
from muckrock.portal.portals.automated import PortalAutoReceiveMixin
from muckrock.portal.portals.manual import ManualPortal
from muckrock.portal.tasks import portal_task


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
                sent_datetime=datetime.now(),
                portal=self.portal,
                direction='incoming',
                )

    def document_reply(self, comm):
        """Process incoming documents"""
        p_file_available = re.compile(r'There are eFOIA files available for you to download')
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
