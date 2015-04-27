"""
Tests for the FOIACommunication model
"""

from datetime import datetime

from django import test

from muckrock.foia.models.communication import FOIACommunication

import nose

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

class TestCommunicationActions(test.TestCase):
    """Tests actions taken upon communications"""

    # fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
    #            'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
    #            'test_foiacommunications.json']

    def setUp(self):
        self.comm = FOIACommunication.objects.create(date=datetime.now(), from_who='Test Sender')

    def test_move(self):
        """Should make a copy of the communication and attach to all the given FOIAs"""
        ok_(False, 'Should test the move method')

    def test_resend(self):
        """Should resubmit the FOIA containing the communication"""
        ok_(False, 'Should test the resend method')

    def tearDown(self):
        self.comm = None


