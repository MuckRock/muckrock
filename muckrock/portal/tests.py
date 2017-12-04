# -*- coding: utf-8 -*-
"""
Tests for the portal application
"""

from django.test import TestCase

from nose.tools import eq_, ok_

from muckrock.factories import FOIACommunicationFactory
from muckrock.portal.models import Portal
from muckrock.task.models import PortalTask

# pylint: disable=no-self-use

class TestManualPortal(TestCase):
    """Test cases for the manual portal integration"""

    def setUp(self):
        """All tests need a manual portal"""
        self.portal = Portal.objects.create(
                url='https://www.example.com',
                name='Test Portal',
                type='other', # use manual logic
                )

    def test_send_msg(self):
        """Sending a message should create a portal task"""
        comm = FOIACommunicationFactory()
        self.portal.send_msg(comm)
        ok_(PortalTask.objects
                .filter(
                    category='n',
                    communication=comm,
                    )
                .exists()
                )

    def test_receive_msg(self):
        """Receiving a message should create a portal task"""
        comm = FOIACommunicationFactory()
        self.portal.receive_msg(comm)
        ok_(PortalTask.objects
                .filter(
                    category='i',
                    communication=comm,
                    )
                .exists()
                )

    def test_get_new_password(self):
        """Should generate a random password"""
        password = self.portal.get_new_password()
        eq_(len(password), 12)


class TestNextRequestPortal(TestCase):
    """Test cases for the NextRequest portal integration"""

    def setUp(self):
        """All tests need a manual portal"""
        self.portal = Portal.objects.create(
                url='https://www.example.com',
                name='Test Portal',
                type='nextrequest',
                )

    def test_confirm_open(self):
        """Test receiving a confirmation message"""
        comm = FOIACommunicationFactory(
                subject='Your first record request 17-1 has been opened.',
                communication=
                ' -- Write ABOVE THIS LINE to post a message that will be sent '
                'to staff. --\n\n'
                'Your first Evanston record request (request number 17-764) '
                'has been submitted. It is currently unpublished and is not '
                'available for the general public to view.\n\n'
                'As the requester, you can always see the status of your '
                'request by signing into the Evanston Public Records portal '
                'here. \n',
                foia__status='ack',
                )
        self.portal.receive_msg(comm)
        eq_(comm.foia.status, 'processed')
        eq_(comm.portals.count(), 1)
