"""
Tests for the FOIACommunication model
"""

import datetime

from django import test
from django.core.validators import ValidationError

from muckrock.foia.models.communication import FOIACommunication
from muckrock import task

import logging
import nose

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

class TestCommunicationActions(test.TestCase):
    """Tests actions taken upon communications"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        self.creation_date = datetime.datetime.now() - datetime.timedelta(1)
        self.comm = FOIACommunication.objects.get(id=1)
        self.comm.date = self.creation_date
        self.comm.save()

    def test_move(self):
        """Should make a copy of the communication and attach to all the given FOIAs"""
        ok_(False, 'Should test the move method')

    def test_resend_sans_email(self):
        """Should resubmit the FOIA containing the communication as a snail mail"""
        self.comm.resend()
        ok_(self.comm.date > self.creation_date,
            'Resubmitting the communication should update the date.')
        eq_(self.comm.foia.status, 'submitted',
            'Resubmitting the communication should resubmit its associated FOIARequest.')

    def test_resend_with_email(self):
        """Should resubmit the FOIA containing the communication automatically"""
        new_email = 'test@example.com'
        self.comm.resend(new_email)
        eq_(self.comm.foia.email, new_email,
            'Resubmitting with a new email should update the email of the FOIA request.')
        eq_(self.comm.foia.status, 'submitted',
            'Resubmitting with an email should resubmit its associated FOIARequest.')

    @raises(ValidationError)
    def test_resend_bad_email(self):
        """Should throw an error if given an invalid email"""
        self.comm.resend('asdfads')

    @raises(ValueError)
    def test_resend_orphan_communication(self):
        """Should throw and error if the communication being resent is an orphan"""
        self.comm.foia = None
        self.comm.save()
        self.comm.resend('hello@world.com')

    def tearDown(self):
        self.comm = None


