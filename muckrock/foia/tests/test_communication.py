"""
Tests for the FOIACommunication model
"""

# Django
from django import test

# Standard Library
import logging
import os

# Third Party
import pytest
from mock import patch

# MuckRock
from muckrock.communication.models import EmailAddress
from muckrock.core.factories import UserFactory
from muckrock.core.test_utils import RunCommitHooksMixin
from muckrock.foia.factories import (
    FOIACommunicationFactory,
    FOIAFileFactory,
    FOIARequestFactory,
)
from muckrock.foia.models import CommunicationMoveLog, FOIACommunication


class TestCommunication(test.TestCase):
    """Tests communication methods"""

    def setUp(self):
        self.foia = FOIARequestFactory()
        self.comm = FOIACommunicationFactory(
            foia=self.foia,
            email__from_email=EmailAddress.objects.fetch("Test Email <test@email.com>"),
        )
        self.file = FOIAFileFactory(comm=self.comm)
        assert self.comm.files.count() == 1

    def test_primary_contact(self):
        """Makes the primary email of the FOIA to the email the communication was
        sent from."""
        self.comm.make_sender_primary_contact()
        self.foia.refresh_from_db()
        assert self.foia.email == self.comm.emails.first().from_email

    def test_attach_file_with_file(self):
        """Test attaching a file with an actual file"""
        try:
            comm = FOIACommunicationFactory()
            with open("tmp.txt", "w", encoding="utf8") as file_:
                file_.write("The file contents")
            with open("tmp.txt", "r", encoding="utf8") as file_:
                comm.attach_file(file_=file_)
            assert comm.files.count() == 1
            foia_file = comm.files.first()
            assert foia_file.title == "tmp"
            assert foia_file.ffile.file.name == "tmp.txt"
            assert foia_file.ffile.read() == "The file contents"
        finally:
            try:
                os.remove("tmp.txt")
            except OSError:
                pass

    def test_attach_file_with_content(self):
        """Test attaching a file with n memory content"""
        comm = FOIACommunicationFactory()
        comm.attach_file(content="More contents", name="doc.pdf")
        assert comm.files.count() == 1
        foia_file = comm.files.first()
        assert foia_file.title == "doc"
        assert foia_file.ffile.file.name == "doc.pdf"
        assert foia_file.ffile.read() == "More contents"

    def test_orphan_error(self):
        """Orphans should raise an error"""
        self.comm.foia = None
        with pytest.raises(ValueError):
            self.comm.make_sender_primary_contact()

    def test_bad_sender(self):
        """Comms with bad sender email should not change contact information"""
        email = self.comm.emails.first()
        email.from_email = None
        foia_email = self.foia.email
        email.save()
        self.comm.make_sender_primary_contact()
        self.foia.refresh_from_db()
        assert self.foia.email == foia_email


class TestCommunicationMove(RunCommitHooksMixin, test.TestCase):
    """Tests the move method"""

    def setUp(self):
        self.foia1 = FOIARequestFactory()
        self.foia2 = FOIARequestFactory()
        self.comm = FOIACommunicationFactory(foia=self.foia1)
        self.file = FOIAFileFactory(comm=self.comm)
        assert self.comm.files.count() == 1
        self.user = UserFactory()

    @patch("muckrock.foia.tasks.upload_document_cloud.delay")
    def test_move_single_comm(self, mock_upload):
        """Should change the request associated with the communication."""
        moved_comms = self.comm.move([self.foia2.pk], self.user)
        assert len(moved_comms) == 1, "Move function should only return one item"
        moved_comm = moved_comms[0]
        assert (
            moved_comm == self.comm
        ), "Communication returned should be the same as the one acted on."
        assert (
            moved_comm.foia.id == self.foia2.id
        ), "Should change the FOIA associated with the communication."
        moved_files = moved_comm.files.all()
        moved_file = moved_files[0]
        logging.debug(
            "File foia: %d; Expected: %d", moved_file.comm.foia.id, self.foia2.id
        )
        assert (
            moved_file.comm == self.comm
        ), "Should not have changed the communication associated with the file."
        # a move log should be generated
        assert CommunicationMoveLog.objects.filter(
            communication=moved_comm, foia=self.foia1, user=self.user
        ).exists()

        self.run_commit_hooks()
        mock_upload.assert_called()

    @patch("muckrock.foia.tasks.upload_document_cloud.delay")
    def test_move_multi_comms(self, mock_upload):
        """Should move the comm to the first request, then clone it to the rest."""
        comm_count = FOIACommunication.objects.count()
        comms = self.comm.move([self.foia1.id, self.foia2.id], self.user)
        # + 1 communications created
        self.comm.refresh_from_db()
        assert (
            self.comm.foia.id == self.foia1.id
        ), "The communication should be moved to the first listed request."
        assert (
            FOIACommunication.objects.count() == comm_count + 1
        ), "A clone should be made for each additional request in the list."
        assert (
            len(comms) == 2
        ), "Two communications should be returned, since two were operated on."
        assert (
            self.comm.pk == comms[0].pk
        ), "The first communication in the list should be this one."
        assert (
            comms[1].pk is not self.comm.pk
        ), "The second communication should be a new one, since it was cloned."
        # each comm should have a move log generated for it
        for comm in comms:
            assert CommunicationMoveLog.objects.filter(
                communication=comm, foia=self.foia1, user=self.user
            ).exists()
        self.run_commit_hooks()
        mock_upload.assert_called()

    def test_move_invalid_foia(self):
        """Should raise an error if trying to call move on invalid request pks."""
        original_request = self.comm.foia.id
        with pytest.raises(ValueError):
            self.comm.move("abc", self.user)
        self.comm.refresh_from_db()
        assert (
            self.comm.foia.id == original_request
        ), "If something goes wrong, the move should not complete."

    def test_move_empty_list(self):
        """Should raise an error if trying to call move on an empty list."""
        original_request = self.comm.foia.id
        with pytest.raises(ValueError):
            self.comm.move([], self.user)
        self.comm.refresh_from_db()
        assert (
            self.comm.foia.id == original_request
        ), "If something goes wrong, the move should not complete."

    def test_move_missing_ffile(self):
        """
        The move operation should not crash when FOIAFile has a null ffile field.
        """
        self.file.ffile = None
        self.file.save()
        assert not self.comm.files.all()[0].ffile
        self.comm.move([self.foia2.pk], self.user)


class TestCommunicationClone(RunCommitHooksMixin, test.TestCase):
    """Tests the clone method"""

    def setUp(self):
        self.comm = FOIACommunicationFactory()
        self.file = FOIAFileFactory(comm=self.comm)
        assert self.file in self.comm.files.all()
        self.user = UserFactory()

    @patch("muckrock.foia.tasks.upload_document_cloud.delay")
    def test_clone_single(self, mock_upload):
        """Should duplicate the communication to the request."""
        other_foia = FOIARequestFactory()
        comm_count = FOIACommunication.objects.count()
        comm_pk = self.comm.pk
        clone_comm = self.comm.clone([other_foia], self.user)
        # + 1 communications
        assert (
            FOIACommunication.objects.count() == comm_count + 1
        ), "Should clone the request once."
        assert (
            self.comm.pk == comm_pk
        ), "The identity of the communication that calls clone should not change."
        # a move log should be generated for cloned request
        assert CommunicationMoveLog.objects.filter(
            communication=clone_comm[0], foia=self.comm.foia, user=self.user
        ).exists()
        # a move log should not be generated for the original request
        assert not CommunicationMoveLog.objects.filter(communication=self.comm).exists()
        self.run_commit_hooks()
        mock_upload.assert_called()

    @patch("muckrock.foia.tasks.upload_document_cloud.delay")
    def test_clone_multi(self, mock_upload):
        """Should duplicate the communication to each request in the list."""
        first_foia = FOIARequestFactory()
        second_foia = FOIARequestFactory()
        third_foia = FOIARequestFactory()
        comm_count = FOIACommunication.objects.count()
        clones = self.comm.clone([first_foia, second_foia, third_foia], self.user)
        # + 3 communications
        assert (
            FOIACommunication.objects.count() == comm_count + 3
        ), "Should clone the request twice."
        assert (
            clones[0].pk is not clones[1].pk is not clones[2].pk
        ), "The returned list should contain unique communcation objects."
        # a move log should be generated for each cloned request
        for clone in clones:
            assert CommunicationMoveLog.objects.filter(
                communication=clone, foia=self.comm.foia, user=self.user
            ).exists()
        self.run_commit_hooks()
        mock_upload.assert_called()

    @patch("muckrock.foia.tasks.upload_document_cloud.delay")
    def test_clone_files(self, mock_upload):
        """Should duplicate all the files for each communication."""
        first_foia = FOIARequestFactory()
        second_foia = FOIARequestFactory()
        third_foia = FOIARequestFactory()
        file_count = self.comm.files.count()
        clones = self.comm.clone([first_foia, second_foia, third_foia], self.user)
        for each_clone in clones:
            assert (
                each_clone.files.count() == file_count
            ), "Each clone should have its own set of files."
        self.run_commit_hooks()
        mock_upload.assert_called()

    def test_clone_empty_list(self):
        """Should throw a value error if given an empty list"""
        with pytest.raises(ValueError):
            self.comm.clone([], self.user)

    def test_clone_bad_pk(self):
        """Should throw an error if bad foia PK given"""
        with pytest.raises(ValueError):
            self.comm.clone("abc", self.user)

    def test_clone_missing_ffile(self):
        """
        The clone operation should not crash when FOIAFile has a null ffile field.
        """
        self.file.ffile = None
        self.file.save()
        assert not self.comm.files.all()[0].ffile
        other_foia = FOIARequestFactory()
        self.comm.clone([other_foia], self.user)
