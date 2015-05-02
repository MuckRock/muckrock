"""
Tests for the FOIACommunication model
"""

import datetime

from django import test
from django.core.validators import ValidationError

from muckrock.foia.models.communication import FOIACommunication
from muckrock.foia.models.request import FOIARequest

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
        self.foia1 = FOIARequest.objects.get(id=1)
        self.foia2 = FOIARequest.objects.get(id=2)

    def test_move_single_foia(self):
        """Should change the request associated with the communication."""
        comms = self.comm.move(self.foia2.id)
        eq_(self.comm.foia.id, self.foia2.id,
            'Should change the FOIA associated with the communication.')
        for file_ in self.comm.files.all():
            eq_(file_.foia.id, self.foia2.id,
                'Should also change the files to reference the destination FOIA.')
        eq_(self.comm, comms[0], 'Should this comm as the one operated on.')

    def test_move_multi_foias(self):
        """Should move the comm to the first request, then clone it to the rest."""
        comm_count = FOIACommunication.objects.count()
        comms = self.comm.move([self.foia1.id, self.foia2.id])
        # + 1 communications created
        updated_comm = FOIACommunication.objects.get(pk=self.comm_pk)
        eq_(updated_comm.foia.id, self.foia1.id,
            'The communication should be moved to the first listed request.')
        eq_(FOIACommunication.objects.count(), comm_count + 1,
            'A clone should be made for each additional request in the list.')
        eq_(len(comms), 2,
            'Two communications should be returned, since two were operated on.')
        eq_(updated_comm.pk, comms[0].pk,
            'The first communication in the list should be this one.')
        ok_(comms[1].pk is not updated_comm.pk,
            'The second communication should be a new one, since it was cloned.')

    @raises(ValueError)
    def test_move_invalid_foia(self):
        """Should raise an error if trying to call move on invalid request pks."""
        original_request = self.comm.foia.id
        self.comm.move('abc')
        eq_(FOIACommunication.objects.get(pk=self.comm_pk).foia.id, original_request,
            'If something goes wrong, the move should not complete.')

    @raises(ValueError)
    def test_move_empty_list(self):
        """Should raise an error if trying to call move on an empty list."""
        original_request = self.comm.foia.id
        self.comm.move([])
        eq_(FOIACommunication.objects.get(pk=self.comm_pk).foia.id, original_request,
            'If something goes wrong, the move should not complete.')

class TestCommunicationClone(test.TestCase):
    """Tests the clone method"""

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        self.comm = FOIACommunication.objects.get(id=1)

    def test_clone_single(self):
        """Should duplicate the communication to the request."""
        comm_count = FOIACommunication.objects.count()
        self.comm.clone(2)
        # + 1 communications
        eq_(FOIACommunication.objects.count(), comm_count + 1,
            'Should clone the request once.')
        eq_(self.comm.pk, 1,
            'The identity of the communication that calls clone should not change.')

    def test_clone_multi(self):
        """Should duplicate the communication to each request in the list."""
        comm_count = FOIACommunication.objects.count()
        clones = self.comm.clone([2, 3, 4])
        # + 3 communications
        eq_(FOIACommunication.objects.count(), comm_count + 3,
            'Should clone the request twice.')
        ok_(clones[0].pk is not clones[1].pk is not clones[2].pk,
            'The returned list should contain unique communcation objects.')

    def test_clone_files(self):
        """Should duplicate all the files for each communication."""
        file_count = self.comm.files.count()
        clones = self.comm.clone([2, 3, 4])
        for each_clone in clones:
            eq_(each_clone.files.count(), file_count,
                'Each clone should have its own set of files')

    @raises(ValueError)
    def test_clone_empty_list(self):
        """Should throw a value error if given an empty list"""
        self.comm.clone([])

    @raises(ValueError)
    def test_clone_bad_pk(self):
        """Should throw an error if bad foia PK given"""
        self.comm.clone('abc')

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
    def test_resend_orphan_comm(self):
        """Should throw and error if the communication being resent is an orphan"""
        self.comm.foia = None
        self.comm.save()
        self.comm.resend('hello@world.com')
