"""
Tests for the FOIACommunication model
"""

import datetime

from django import test
from django.core.validators import ValidationError

from muckrock.foia.models.communication import FOIACommunication
from muckrock.foia.models.request import FOIARequest
from muckrock import task

import logging
import nose

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

class TestCommunicationMove(test.TestCase):
    """Tests the move method"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        self.comm = FOIACommunication.objects.get(id=1)
        self.comm_pk = self.comm.pk
        self.f1 = FOIARequest.objects.get(id=1)
        self.f2 = FOIARequest.objects.get(id=2)

    def test_move_single_foia(self):
        """Should make a copy of the communication to the request, then delete the original."""
        eq_(self.f2.communications.count(), 1,
            'Request should only have one communication.')
        self.comm.move(self.f2.id)
        eq_(self.f2.communications.count(), 2,
            'Moving the communication should copy it to that request.')
        ok_(not FOIACommunication.objects.filter(pk=self.comm_pk),
            'Moving the communication should delete the original.')

    def test_move_multi_foias(self):
        """Should make a copy of the communication for each FOIA it is moved to, then delete the original."""
        comm_count = FOIACommunication.objects.count()
        self.comm.move([self.f1.id, self.f2.id])
        # + 2 communications created
        # - 1 communications celeted
        eq_(FOIACommunication.objects.count(), comm_count + 2 - 1,
            'A new communication should be made for each request.')
        ok_(not FOIACommunication.objects.filter(pk=self.comm_pk),
            'Moving the communication should delete the original.')

    @raises(ValueError)
    def test_move_invalid_foias(self):
        """Should raise an error if trying to call move on invalid request pks."""
        self.comm.move(['abc', 123])
        ok_(FOIACommunication.objects.filter(pk=self.comm_pk),
            'If something goes wrong, the original should not be deleted.')

    @raises(ValueError)
    def test_move_empty_list(self):
        """Should raise an error if trying to call move on an empty list."""
        self.comm.move([])
        ok_(FOIACommunication.objects.filter(pk=self.comm_pk),
            'If something goes wrong, the original should not be deleted.')

class TestCommunicationResend(test.TestCase):
    """Tests the resend method"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        self.creation_date = datetime.datetime.now() - datetime.timedelta(1)
        self.comm = FOIACommunication.objects.get(id=1)
        self.comm.date = self.creation_date
        self.comm.save()

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
