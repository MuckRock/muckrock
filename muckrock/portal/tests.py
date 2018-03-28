# -*- coding: utf-8 -*-
"""
Tests for the portal application
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date

# Third Party
import requests_mock
from mock import patch
from nose.tools import assert_false, eq_, ok_

# MuckRock
from muckrock.foia.factories import FOIACommunicationFactory
from muckrock.foia.models.communication import FOIACommunication
from muckrock.portal.models import Portal
from muckrock.task.models import PortalTask


class TestManualPortal(TestCase):
    """Test cases for the manual portal integration"""

    def setUp(self):
        """All tests need a manual portal"""
        self.portal = Portal.objects.create(
            url='https://www.example.com',
            name='Test Portal',
            type='other',  # use manual logic
        )

    def test_send_msg(self):
        """Sending a message should create a portal task"""
        comm = FOIACommunicationFactory()
        self.portal.send_msg(comm)
        ok_(
            PortalTask.objects.filter(
                category='n',
                communication=comm,
            ).exists()
        )

    def test_receive_msg(self):
        """Receiving a message should create a portal task"""
        comm = FOIACommunicationFactory()
        self.portal.receive_msg(comm)
        ok_(
            PortalTask.objects.filter(
                category='i',
                communication=comm,
            ).exists()
        )

    def test_get_new_password(self):
        """Should generate a random password"""
        password = self.portal.get_new_password()
        eq_(len(password), 12)


class TestNextRequestPortal(TestCase):
    """Test cases for the NextRequest portal integration"""

    def setUp(self):
        """All tests need a NextRequest portal"""
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
        comm = FOIACommunication.objects.get(pk=comm.pk)
        eq_(comm.foia.status, 'processed')
        eq_(comm.foia.current_tracking_id(), '17-1')
        eq_(
            comm.communication,
            'Your first Evanston record request (request number 17-764) '
            'has been submitted. It is currently unpublished and is not '
            'available for the general public to view.\n\n',
        )
        assert_false(comm.hidden)
        eq_(comm.portals.count(), 1)

    def test_text_reply(self):
        """Test receiving a normal reply"""
        comm = FOIACommunicationFactory(
            subject='[External Message Added]',
            communication=
            'A message was sent to you regarding record request #17-1:\n'
            'This is the reply\n'
            'View Request',
            foia__status='processed',
        )
        self.portal.receive_msg(comm)
        eq_(comm.foia.status, 'processed')
        eq_(comm.communication, '\nThis is the reply\n')
        assert_false(comm.hidden)
        eq_(comm.portals.count(), 1)
        eq_(comm.responsetask_set.count(), 1)

    def test_due_date(self):
        """Test receiving a due date reply"""
        comm = FOIACommunicationFactory(
            subject='[Due Date Changed]',
            communication='The due date for record request #18-209 has been '
            'changed to: March 16, 2018\nView Request #18-209',
            foia__status='processed',
        )
        self.portal.receive_msg(comm)
        eq_(comm.foia.status, 'processed')
        eq_(
            comm.communication, 'The due date for record request #18-209 has '
            'been changed to: March 16, 2018'
        )
        assert_false(comm.hidden)
        eq_(comm.foia.date_estimate, date(2018, 3, 16))


class TestFBIPortal(TestCase):
    """Test cases for the FBI portal integration"""

    def setUp(self):
        """All tests need a FBI portal"""
        self.portal = Portal.objects.create(
            url='https://www.example.com',
            name='Test Portal',
            type='fbi',
        )

    def test_confirm_open(self):
        """Test receiving a confirmation message"""
        comm = FOIACommunicationFactory(
            subject='eFOIA Request Received',
            foia__status='ack',
        )
        self.portal.receive_msg(comm)
        eq_(comm.foia.status, 'processed')
        eq_(comm.portals.count(), 1)

    @requests_mock.Mocker()
    @patch('muckrock.foia.tasks.upload_document_cloud.apply_async')
    @patch('muckrock.foia.tasks.classify_status.apply_async')
    def test_document_reply(self, mock_requests, mock_upload, mock_classify):
        """Test receiving a confirmation message"""
        # pylint: disable=unused-argument
        mock_requests.get(
            'https://www.example.com/file1.pdf',
            text='File 1 Content',
        )
        mock_requests.get(
            'https://www.example.com/file2.pdf',
            text='File 2 Content',
        )
        comm = FOIACommunicationFactory(
            subject='eFOIA files available',
            communication='There are eFOIA files available for you to download\n'
            '* [file1.pdf](https://www.example.com/file1.pdf)\n'
            '* [file2.pdf](https://www.example.com/file2.pdf)\n'
        )
        self.portal.receive_msg(comm)
        eq_(comm.files.count(), 2)
        eq_(comm.files.all()[0].ffile.read(), 'File 1 Content')
        eq_(comm.files.all()[1].ffile.read(), 'File 2 Content')
        eq_(comm.portals.count(), 1)
        eq_(comm.responsetask_set.count(), 1)
