"""
Tests for the FOIACommunication model
"""

import datetime

from django import test
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.core.validators import ValidationError

from muckrock import factories
from muckrock.accounts.models import AgencyUser
from muckrock.foia.models.communication import FOIACommunication
from muckrock.foia.models.request import FOIARequest
from muckrock.foia.models.file import FOIAFile
from muckrock.foia.views import raw
from muckrock.utils import unique_username

import logging
from nose.tools import ok_, eq_, raises, assert_raises


class TestCommunication(test.TestCase):
    """Tests communication methods"""

    def test_primary_contact(self):
        """Makes the primary email of the FOIA to the email the communication was sent from."""
        comm = factories.FOIACommunicationFactory()
        comm.make_sender_primary_contact()
        eq_(comm.foia.get_emails(), ([comm.from_user.email], []))

    @raises(ValueError)
    def test_orphan_error(self):
        """Orphans should raise an error"""
        comm = factories.FOIACommunicationFactory(foia=None)
        comm.make_sender_primary_contact()


class TestCommunicationMove(test.TestCase):
    """Tests the move method"""

    def test_move_single_comm(self):
        """Should change the request associated with the communication."""
        file_ = factories.FOIAFileFactory()
        comm = file_.comm
        foia = factories.FOIARequestFactory()

        moved_comms = comm.move(foia.id)
        eq_(len(moved_comms), 1,
            'Move function should only return one item')
        moved_comm = moved_comms[0]
        eq_(moved_comm, comm,
            'Communication returned should be the same as the one acted on.')
        eq_(moved_comm.foia.id, foia.id,
            'Should change the FOIA associated with the communication.')
        moved_files = moved_comm.files.all()
        moved_file = moved_files[0]
        logging.debug('File foia: %d; Expected: %d', moved_file.foia.id, foia.id)
        eq_(moved_file.foia, foia,
            'Should also change the files to reference the destination FOIA.')
        eq_(moved_file.comm, comm,
            'Should not have changed the communication associated with the file.')

    def test_move_multi_comms(self):
        """Should move the comm to the first request, then clone it to the rest."""
        file_ = factories.FOIAFileFactory()
        comm = file_.comm
        foia1 = comm.foia
        foia2 = factories.FOIARequestFactory()

        comm_count = FOIACommunication.objects.count()
        comms = comm.move([foia1.id, foia2.id])
        # + 1 communications created
        updated_comm = FOIACommunication.objects.get(pk=comm.pk)
        eq_(updated_comm.foia.id, foia1.id,
            'The communication should be moved to the first listed request.')
        eq_(FOIACommunication.objects.count(), comm_count + 1,
            'A clone should be made for each additional request in the list.')
        eq_(len(comms), 2,
            'Two communications should be returned, since two were operated on.')
        eq_(updated_comm.pk, comms[0].pk,
            'The first communication in the list should be this one.')
        ok_(comms[1].pk is not updated_comm.pk,
            'The second communication should be a new one, since it was cloned.')

    def test_move_invalid_foia(self):
        """Should raise an error if trying to call move on invalid request pks."""
        comm = factories.FOIACommunicationFactory()
        original_request = comm.foia.id
        with assert_raises(ValueError):
            comm.move('abc')
        eq_(FOIACommunication.objects.get(pk=comm.pk).foia.id, original_request,
            'If something goes wrong, the move should not complete.')

    def test_move_empty_list(self):
        """Should raise an error if trying to call move on an empty list."""
        comm = factories.FOIACommunicationFactory()
        original_request = comm.foia.id
        with assert_raises(ValueError):
            comm.move([])
        eq_(FOIACommunication.objects.get(pk=comm.pk).foia.id, original_request,
            'If something goes wrong, the move should not complete.')

    def test_move_missing_ffile(self):
        """
        The move operation should not crash when FOIAFile has a null ffile field.
        """
        foia = factories.FOIARequestFactory()
        file_ = factories.FOIAFileFactory(ffile=None)
        comm = file_.comm
        ok_(not comm.files.all()[0].ffile)
        comm.move(foia.id)


class TestCommunicationClone(test.TestCase):
    """Tests the clone method"""

    def test_clone_single(self):
        """Should duplicate the communication to the request."""
        comm = factories.FOIACommunicationFactory()
        foia = factories.FOIARequestFactory()
        comm_pk = comm.pk

        comm_count = FOIACommunication.objects.count()
        comm.clone(foia.pk)
        # + 1 communications
        eq_(FOIACommunication.objects.count(), comm_count + 1,
            'Should clone the request once.')
        eq_(comm.pk, comm_pk,
            'The identity of the communication that calls clone should not change.')

    def test_clone_multi(self):
        """Should duplicate the communication to each request in the list."""
        comm = factories.FOIACommunicationFactory()
        foias = factories.FOIARequestFactory.create_batch(3)

        comm_count = FOIACommunication.objects.count()
        clones = comm.clone([f.pk for f in foias])
        # + 3 communications
        eq_(FOIACommunication.objects.count(), comm_count + 3,
            'Should clone the request twice.')
        ok_(clones[0].pk is not clones[1].pk is not clones[2].pk,
            'The returned list should contain unique communcation objects.')

    def test_clone_files(self):
        """Should duplicate all the files for each communication."""
        file_ = factories.FOIAFileFactory()
        comm = file_.comm
        foias = factories.FOIARequestFactory.create_batch(3)

        file_count = comm.files.count()
        clones = comm.clone([f.pk for f in foias])
        for each_clone in clones:
            eq_(each_clone.files.count(), file_count,
                    'Each clone should have its own set of files')

    @raises(ValueError)
    def test_clone_empty_list(self):
        """Should throw a value error if given an empty list"""
        comm = factories.FOIACommunicationFactory()
        comm.clone([])

    @raises(ValueError)
    def test_clone_bad_pk(self):
        """Should throw an error if bad foia PK given"""
        comm = factories.FOIACommunicationFactory()
        comm.clone('abc')

    def test_clone_missing_ffile(self):
        """
        The clone operation should not crash when FOIAFile has a null ffile field.
        """
        file_ = factories.FOIAFileFactory(ffile=None)
        comm = file_.comm
        foia = factories.FOIARequestFactory()
        ok_(not comm.files.all()[0].ffile)
        comm.clone(foia.pk)


class TestCommunicationResend(test.TestCase):
    """Tests the resend method"""

    def test_resend_with_email(self):
        """Should resubmit the FOIA containing the communication automatically"""
        new_email = 'test@example.com'
        user = factories.AgencyUserFactory(email=new_email, username=new_email)
        creation_date = datetime.datetime.now() - datetime.timedelta(1)
        comm = factories.FOIACommunicationFactory(date=creation_date)

        comm.resend([user])
        ok_(comm.date > creation_date,
            'Resubmitting the communication should update the date.')
        eq_(comm.foia.get_emails(), ([new_email], []),
            'Resubmitting with a new email should update the email of the FOIA request.')
        eq_(comm.foia.status, 'ack',
            'Resubmitting with an email should resubmit its associated FOIARequest.')

    @raises(ValueError)
    def test_resend_orphan_comm(self):
        """Should throw an error if the communication being resent is an orphan"""
        comm = factories.FOIACommunicationFactory(foia=None)
        new_email = 'test@example.com'
        user = factories.AgencyUserFactory(email=new_email, username=new_email)
        comm.resend([user])

    @raises(ValueError)
    def test_resend_unapproved_comm(self):
        """Should throw an error if the communication being resent has an unapproved agency"""
        comm = factories.FOIACommunicationFactory(foia__agency__status='rejected')
        new_email = 'test@example.com'
        user = factories.AgencyUserFactory(email=new_email, username=new_email)
        comm.resend([user])


class TestRawEmail(test.TestCase):
    """Tests the raw email view"""

    def test_raw_email_view(self):
        """Advanced users should be able to view raw emails"""
        basic_user = factories.UserFactory(profile__acct_type='basic')
        pro_user = factories.UserFactory(profile__acct_type='pro')
        comm = factories.FOIACommunicationFactory()

        url = reverse('foia-raw', kwargs={'idx': comm.id})
        request = test.RequestFactory().get(url)
        request.user = basic_user

        response = raw(request, comm.id)
        eq_(response.status_code, 302, 'Basic users should be denied access.')
        request.user = pro_user
        response = raw(request, comm.id)
        eq_(response.status_code, 200, 'Advanced users should be allowed access.')
