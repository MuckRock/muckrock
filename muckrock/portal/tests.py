# -*- coding: utf-8 -*-
"""
Tests for the portal application
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date
from unittest.mock import Mock, patch

# Third Party
import pytest
import requests
import requests_mock

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
            url="https://www.example.com",
            name="Test Portal",
            type="other",  # use manual logic
        )

    def test_send_msg(self):
        """Sending a message should create a portal task"""
        comm = FOIACommunicationFactory(category="n")
        self.portal.send_msg(comm)
        assert PortalTask.objects.filter(category="n", communication=comm).exists()

    def test_receive_msg(self):
        """Receiving a message should create a portal task"""
        comm = FOIACommunicationFactory()
        self.portal.receive_msg(comm)
        assert PortalTask.objects.filter(category="i", communication=comm).exists()

    def test_get_new_password(self):
        """Should generate a random password"""
        password = self.portal.get_new_password()
        assert len(password) == 12


@pytest.mark.skip("not currently used")
class _TestNextRequestPortal(TestCase):
    """Test cases for the NextRequest portal integration"""

    def setUp(self):
        """All tests need a NextRequest portal"""
        self.portal = Portal.objects.create(
            url="https://www.example.com", name="Test Portal", type="nextrequest"
        )

    def test_confirm_open(self):
        """Test receiving a confirmation message"""
        comm = FOIACommunicationFactory(
            subject="Your first record request 17-1 has been opened.",
            communication=" -- Write ABOVE THIS LINE to post a message that will "
            "be sent to staff. --\n\n"
            "Your first Evanston record request (request number 17-764) "
            "has been submitted. It is currently unpublished and is not "
            "available for the general public to view.\n\n"
            "As the requester, you can always see the status of your "
            "request by signing into the Evanston Public Records portal "
            "here. \n",
            foia__status="ack",
        )
        self.portal.receive_msg(comm)
        comm = FOIACommunication.objects.get(pk=comm.pk)
        assert comm.foia.status == "processed"
        assert comm.foia.current_tracking_id() == "17-1"
        assert (
            comm.communication
            == "Your first Evanston record request (request number 17-764) "
            "has been submitted. It is currently unpublished and is not "
            "available for the general public to view.\n\n"
        )
        assert not comm.hidden
        assert comm.portals.count() == 1

    def test_text_reply(self):
        """Test receiving a normal reply"""
        comm = FOIACommunicationFactory(
            subject="[External Message Added]",
            communication="A message was sent to you regarding record request #17-1:\n"
            "This is the reply\n"
            "View Request",
            foia__status="processed",
        )
        self.portal.receive_msg(comm)
        assert comm.foia.status == "processed"
        assert comm.communication == "\nThis is the reply\n"
        assert not comm.hidden
        assert comm.portals.count() == 1
        assert comm.responsetask_set.count() == 1

    def test_due_date(self):
        """Test receiving a due date reply"""
        comm = FOIACommunicationFactory(
            subject="[Due Date Changed]",
            communication="The due date for record request #18-209 has been "
            "changed to: March 16, 2018\nView Request #18-209",
            foia__status="processed",
        )
        self.portal.receive_msg(comm)
        assert comm.foia.status == "processed"
        assert (
            comm.communication == "The due date for record request #18-209 has "
            "been changed to: March 16, 2018"
        )
        assert not comm.hidden
        assert comm.foia.date_estimate == date(2018, 3, 16)


class TestFBIPortal(TestCase):
    """Test cases for the FBI portal integration"""

    def setUp(self):
        """All tests need a FBI portal"""
        self.portal = Portal.objects.create(
            url="https://www.example.com", name="Test Portal", type="fbi"
        )

    def _set_raw_email(self, comm, plain_body):
        """Put the FBI raw email body on the comm's auto-created raw email.

        document_reply_task parses the raw email; comm.communication is stripped
        to the intro line in production. Setting raw_email_db (not the S3 file)
        is enough -- the raw_email property falls back to it.
        """
        raw = (
            "From: efoia@subscriptions.fbi.gov\r\n"
            "To: test@requests.muckrock.com\r\n"
            "Subject: eFOIA files available\r\n"
            'Content-Type: text/plain; charset="utf-8"\r\n'
            "\r\n" + plain_body
        )
        raw_email = comm.emails.first().rawemail
        raw_email.raw_email_db = raw
        raw_email.save()

    def test_confirm_open(self):
        """Test receiving a confirmation message"""
        comm = FOIACommunicationFactory(
            subject="eFOIA Request Received", foia__status="ack"
        )
        self.portal.receive_msg(comm)
        assert comm.foia.status == "processed"
        assert comm.portals.count() == 1

    @requests_mock.Mocker()
    @patch("muckrock.foia.tasks.upload_document_cloud.apply_async")
    @patch("muckrock.foia.tasks.classify_status.apply_async")
    def test_document_reply(self, mock_requests, mock_upload, mock_classify):
        """Documents are downloaded by POSTing the per-file token to the gate"""
        # pylint: disable=unused-argument
        mock_requests.post(
            "https://www.example.com/file1.pdf",
            content=b"%PDF-1.2 File 1 Content",
            headers={"Content-Type": "application/pdf"},
        )
        mock_requests.post(
            "https://www.example.com/file2.pdf",
            content=b"%PDF-1.2 File 2 Content",
            headers={"Content-Type": "application/pdf"},
        )
        comm = FOIACommunicationFactory(
            subject="eFOIA files available",
            communication="There are eFOIA files available for you to download.",
        )
        self._set_raw_email(
            comm,
            "There are eFOIA files available for you to download.\r\n\r\n"
            "You can download the files at:\r\n\r\n"
            "  * [file1.pdf](https://www.example.com/file1.pdf)\r\n"
            "    * Use this token to access: TOKEN1\r\n"
            "  * [file2.pdf](https://www.example.com/file2.pdf)\r\n"
            "    * Use this token to access: TOKEN2\r\n",
        )
        self.portal.receive_msg(comm)

        posted = {req.url: req.text for req in mock_requests.request_history}
        assert "token=TOKEN1" in posted["https://www.example.com/file1.pdf"]
        assert "token=TOKEN2" in posted["https://www.example.com/file2.pdf"]
        assert "download=Download+File" in posted["https://www.example.com/file1.pdf"]

        assert comm.files.count() == 2
        assert comm.files.all()[0].ffile.read() == b"%PDF-1.2 File 1 Content"
        assert comm.files.all()[1].ffile.read() == b"%PDF-1.2 File 2 Content"
        assert comm.portals.count() == 1
        assert comm.responsetask_set.count() == 1

    @requests_mock.Mocker()
    def test_document_reply_html_gate_falls_back_to_manual(self, mock_requests):
        """A rejected/expired token re-renders the HTML gate at 200 -- must not
        be saved as a file, and should fall back to manual review"""
        mock_requests.post(
            "https://www.example.com/file1.pdf",
            content=b"<!doctype html><html>token gate</html>",
            headers={"Content-Type": "text/html"},
        )
        comm = FOIACommunicationFactory(
            subject="eFOIA files available",
            communication="There are eFOIA files available for you to download.",
        )
        self._set_raw_email(
            comm,
            "There are eFOIA files available for you to download.\r\n\r\n"
            "  * [file1.pdf](https://www.example.com/file1.pdf)\r\n"
            "    * Use this token to access: BADTOKEN\r\n",
        )
        self.portal.receive_msg(comm)

        assert comm.files.count() == 0
        assert PortalTask.objects.filter(communication=comm).exists()

    @requests_mock.Mocker()
    def test_document_reply_unpaired_link_falls_back_to_manual(self, mock_requests):
        """A link without a following token means the format drifted -- fall
        back to manual rather than downloading a subset"""
        comm = FOIACommunicationFactory(
            subject="eFOIA files available",
            communication="There are eFOIA files available for you to download.",
        )
        self._set_raw_email(
            comm,
            "There are eFOIA files available for you to download.\r\n\r\n"
            "  * [file1.pdf](https://www.example.com/file1.pdf)\r\n"
            "    * Use this token to access: TOKEN1\r\n"
            "  * [file2.pdf](https://www.example.com/file2.pdf)\r\n",
        )
        self.portal.receive_msg(comm)

        assert comm.files.count() == 0
        assert not mock_requests.request_history  # never attempted a download
        assert PortalTask.objects.filter(communication=comm).exists()

    @requests_mock.Mocker()
    def test_document_reply_connection_error_falls_back_to_manual(self, mock_requests):
        """A network error that outlives the retries falls back to manual"""
        mock_requests.post(
            "https://www.example.com/file1.pdf",
            exc=requests.exceptions.ConnectionError,
        )
        comm = FOIACommunicationFactory(
            subject="eFOIA files available",
            communication="There are eFOIA files available for you to download.",
        )
        self._set_raw_email(
            comm,
            "There are eFOIA files available for you to download.\r\n\r\n"
            "  * [file1.pdf](https://www.example.com/file1.pdf)\r\n"
            "    * Use this token to access: TOKEN1\r\n",
        )
        self.portal.receive_msg(comm)

        assert comm.files.count() == 0
        assert PortalTask.objects.filter(communication=comm).exists()

    @patch("muckrock.foia.tasks.upload_document_cloud.apply_async")
    @patch("muckrock.foia.tasks.classify_status.apply_async")
    @patch("muckrock.portal.portals.fbi.requests_retry_session")
    def test_document_reply_retries_configured_and_saves(
        self, mock_session_factory, mock_classify, mock_upload
    ):
        """The download uses a session configured to retry POSTs, and the
        returned file is saved. The urllib3 retry itself is library behavior
        exercised by the real session in production; here we confirm the
        session is built for POST retries and the response is attached."""
        # pylint: disable=unused-argument
        ok = Mock(status_code=200, content=b"%PDF-1.2 File 1 Content")
        ok.headers = {"Content-Type": "application/pdf"}
        mock_session = Mock()
        mock_session.post.return_value = ok
        mock_session_factory.return_value = mock_session

        comm = FOIACommunicationFactory(
            subject="eFOIA files available",
            communication="There are eFOIA files available for you to download.",
        )
        self._set_raw_email(
            comm,
            "There are eFOIA files available for you to download.\r\n\r\n"
            "  * [file1.pdf](https://www.example.com/file1.pdf)\r\n"
            "    * Use this token to access: TOKEN1\r\n",
        )
        self.portal.receive_msg(comm)

        # the retrying session was configured to retry POSTs
        _, kwargs = mock_session_factory.call_args
        assert kwargs.get("retries") == 5
        assert kwargs.get("allowed_methods") == frozenset({"POST"})

        # the token was POSTed and the returned file saved
        _, post_kwargs = mock_session.post.call_args
        assert post_kwargs["data"]["token"] == "TOKEN1"
        assert comm.files.count() == 1
        assert comm.files.all()[0].ffile.read() == b"%PDF-1.2 File 1 Content"
        assert comm.responsetask_set.count() == 1
