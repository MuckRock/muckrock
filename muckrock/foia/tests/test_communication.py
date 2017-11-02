"""
Tests for the FOIACommunication model
"""

from django import test
from django.core.urlresolvers import reverse

from muckrock import factories
from muckrock.communication.models import EmailAddress
from muckrock.foia.models.communication import FOIACommunication
from muckrock.foia.views import raw

import logging
import nose

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

class TestCommunication(test.TestCase):
    """Tests communication methods"""
    def setUp(self):
        self.foia = factories.FOIARequestFactory()
        self.comm = factories.FOIACommunicationFactory(
            foia=self.foia,
            email__from_email=EmailAddress.objects.fetch(u'Test Email <test@email.com>'),
        )
        self.file = factories.FOIAFileFactory(comm=self.comm)
        eq_(self.comm.files.count(), 1)

    def test_primary_contact(self):
        """Makes the primary email of the FOIA to the email the communication was sent from."""
        self.comm.make_sender_primary_contact()
        self.foia.refresh_from_db()
        eq_(self.foia.email, self.comm.emails.first().from_email)

    @raises(ValueError)
    def test_orphan_error(self):
        """Orphans should raise an error"""
        self.comm.foia = None
        self.comm.make_sender_primary_contact()

    @raises(ValueError)
    def test_bad_sender_error(self):
        """Comms with bad sender email should raise an error"""
        email = self.comm.emails.first()
        email.from_email = None
        email.save()
        self.comm.make_sender_primary_contact()


class TestCommunicationMove(test.TestCase):
    """Tests the move method"""
    def setUp(self):
        self.foia1 = factories.FOIARequestFactory()
        self.foia2 = factories.FOIARequestFactory()
        self.comm = factories.FOIACommunicationFactory(foia=self.foia1)
        self.file = factories.FOIAFileFactory(comm=self.comm)
        eq_(self.comm.files.count(), 1)

    def test_move_single_comm(self):
        """Should change the request associated with the communication."""
        moved_comms = self.comm.move(self.foia2.id)
        eq_(len(moved_comms), 1,
            'Move function should only return one item')
        moved_comm = moved_comms[0]
        eq_(moved_comm, self.comm,
            'Communication returned should be the same as the one acted on.')
        eq_(moved_comm.foia.id, self.foia2.id,
            'Should change the FOIA associated with the communication.')
        moved_files = moved_comm.files.all()
        moved_file = moved_files[0]
        logging.debug('File foia: %d; Expected: %d', moved_file.foia.id, self.foia2.id)
        eq_(moved_file.foia, self.foia2,
            'Should also change the files to reference the destination FOIA.')
        eq_(moved_file.comm, self.comm,
            'Should not have changed the communication associated with the file.')

    def test_move_multi_comms(self):
        """Should move the comm to the first request, then clone it to the rest."""
        comm_count = FOIACommunication.objects.count()
        comms = self.comm.move([self.foia1.id, self.foia2.id])
        # + 1 communications created
        self.comm.refresh_from_db()
        eq_(self.comm.foia.id, self.foia1.id,
            'The communication should be moved to the first listed request.')
        eq_(FOIACommunication.objects.count(), comm_count + 1,
            'A clone should be made for each additional request in the list.')
        eq_(len(comms), 2,
            'Two communications should be returned, since two were operated on.')
        eq_(self.comm.pk, comms[0].pk,
            'The first communication in the list should be this one.')
        ok_(comms[1].pk is not self.comm.pk,
            'The second communication should be a new one, since it was cloned.')

    @raises(ValueError)
    def test_move_invalid_foia(self):
        """Should raise an error if trying to call move on invalid request pks."""
        original_request = self.comm.foia.id
        self.comm.move('abc')
        self.comm.refresh_from_db()
        eq_(self.comm.foia.id, original_request,
            'If something goes wrong, the move should not complete.')

    @raises(ValueError)
    def test_move_empty_list(self):
        """Should raise an error if trying to call move on an empty list."""
        original_request = self.comm.foia.id
        self.comm.move([])
        self.comm.refresh_from_db()
        eq_(self.comm.foia.id, original_request,
            'If something goes wrong, the move should not complete.')

    def test_move_missing_ffile(self):
        """
        The move operation should not crash when FOIAFile has a null ffile field.
        """
        self.file.ffile = None
        self.file.save()
        ok_(not self.comm.files.all()[0].ffile)
        self.comm.move(self.foia2.id)


class TestCommunicationClone(test.TestCase):
    """Tests the clone method"""
    def setUp(self):
        self.comm = factories.FOIACommunicationFactory()
        self.file = factories.FOIAFileFactory(comm=self.comm)
        ok_(self.file in self.comm.files.all())

    def test_clone_single(self):
        """Should duplicate the communication to the request."""
        other_foia = factories.FOIARequestFactory()
        comm_count = FOIACommunication.objects.count()
        comm_pk = self.comm.pk
        self.comm.clone([other_foia.pk])
        # + 1 communications
        eq_(FOIACommunication.objects.count(), comm_count + 1,
            'Should clone the request once.')
        eq_(self.comm.pk, comm_pk,
            'The identity of the communication that calls clone should not change.')

    def test_clone_multi(self):
        """Should duplicate the communication to each request in the list."""
        first_foia = factories.FOIARequestFactory()
        second_foia = factories.FOIARequestFactory()
        third_foia = factories.FOIARequestFactory()
        comm_count = FOIACommunication.objects.count()
        clones = self.comm.clone([first_foia.pk, second_foia.pk, third_foia.pk])
        # + 3 communications
        eq_(FOIACommunication.objects.count(), comm_count + 3,
            'Should clone the request twice.')
        ok_(clones[0].pk is not clones[1].pk is not clones[2].pk,
            'The returned list should contain unique communcation objects.')

    def test_clone_files(self):
        """Should duplicate all the files for each communication."""
        first_foia = factories.FOIARequestFactory()
        second_foia = factories.FOIARequestFactory()
        third_foia = factories.FOIARequestFactory()
        file_count = self.comm.files.count()
        clones = self.comm.clone([first_foia.pk, second_foia.pk, third_foia.pk])
        for each_clone in clones:
            eq_(each_clone.files.count(), file_count,
                'Each clone should have its own set of files.')

    @raises(ValueError)
    def test_clone_empty_list(self):
        """Should throw a value error if given an empty list"""
        self.comm.clone([])

    @raises(ValueError)
    def test_clone_bad_pk(self):
        """Should throw an error if bad foia PK given"""
        self.comm.clone('abc')

    def test_clone_missing_ffile(self):
        """
        The clone operation should not crash when FOIAFile has a null ffile field.
        """
        self.file.ffile = None
        self.file.save()
        ok_(not self.comm.files.all()[0].ffile)
        other_foia = factories.FOIARequestFactory()
        self.comm.clone([other_foia.pk])


class TestRawEmail(test.TestCase):
    """Tests the raw email view"""
    def setUp(self):
        self.comm = factories.FOIACommunicationFactory()
        self.request_factory = test.RequestFactory()
        self.url = reverse('foia-raw', kwargs={'idx': self.comm.id})
        self.view = raw

    def test_raw_email_view(self):
        """Advanced users should be able to view raw emails"""
        basic_user = factories.UserFactory(profile__acct_type='basic')
        pro_user = factories.UserFactory(profile__acct_type='pro')
        request = self.request_factory.get(self.url)
        request.user = basic_user
        response = self.view(request, self.comm.id)
        eq_(response.status_code, 302, 'Basic users should be denied access.')
        request.user = pro_user
        response = self.view(request, self.comm.id)
        eq_(response.status_code, 200, 'Advanced users should be allowed access.')
