# -*- coding: utf-8 -*-
"""
Tests for the portal application
"""

from django.test import TestCase

from nose.tools import eq_, ok_

from muckrock.factories import FOIACommunicationFactory
from muckrock.portal.portals import ManualPortal
from muckrock.task.models import PortalTask

# pylint: disable=no-self-use

class TestManualPortal(TestCase):
    """Test cases for the manual portal integration"""

    def setUp(self):
        """All tests need a manual portal"""
        self.portal = ManualPortal()

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
