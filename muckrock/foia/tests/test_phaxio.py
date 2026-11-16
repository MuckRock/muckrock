"""
Tests for sending faxes through Phaxio

Phaxio is faked below any client library, so these tests pin down what goes
over the wire rather than how a client is called.
"""

# Django
from celery.exceptions import Retry
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

# Standard Library
from unittest.mock import patch

# MuckRock
from muckrock.communication.models import FaxCommunication, PhoneNumber
from muckrock.core.test_utils import FakeApi
from muckrock.foia.factories import FOIACommunicationFactory, FOIAFileFactory
from muckrock.foia.tasks import send_fax


def phaxio_sent(fax_id=1234):
    """Phaxio's response to a queued fax"""
    return {
        "success": True,
        "message": "Fax queued for sending",
        "data": {"id": fax_id},
    }


def file_parts(request):
    return [part for part in request.parts if part[0] in ("file", "file[]")]


@override_settings(
    PHAXIO_KEY="phaxio_key",
    PHAXIO_SECRET="phaxio_secret",
    PHAXIO_BATCH_DELAY=300,
    MUCKROCK_URL="https://www.muckrock.com",
)
class SendFaxTests(TestCase):
    """Sending a communication by fax through Phaxio"""

    def setUp(self):
        self.comm = FOIACommunicationFactory()
        self.comm.foia.fax = PhoneNumber.objects.create(
            number="617-555-0101", type="fax"
        )
        self.comm.foia.save()

    def test_sends_the_message_to_the_request_fax_number(self):
        with FakeApi("api.phaxio.com") as phaxio:
            phaxio.respond(phaxio_sent())
            send_fax(self.comm.pk, "A" * 60, "Please send the records.", 2)

        assert len(phaxio.requests) == 1
        request = phaxio.requests[0]
        assert request.method == "POST"
        assert request.path == "/v2/faxes"
        assert request.basic_auth == ("phaxio_key", "phaxio_secret")
        fax = FaxCommunication.objects.get(communication=self.comm)
        params = request.params
        assert params["to[]"] == "+16175550101"
        assert params["header_text"] == "A" * 45
        assert params["batch_delay"] == "300"
        assert params["batch_collision_avoidance"] == "true"
        assert params["callback_url"] == "https://www.muckrock.com/mailgun/phaxio/"
        assert params["tag"] == {"fax_id": str(fax.pk), "error_count": "2"}
        assert "test_fail" not in params
        [(_, filename, payload)] = file_parts(request)
        assert filename.endswith(".txt")
        assert payload == b"Please send the records."

    def test_records_the_phaxio_fax_id(self):
        with FakeApi("api.phaxio.com") as phaxio:
            phaxio.respond(phaxio_sent(fax_id=98765))
            send_fax(self.comm.pk, "Subject", "Body", 0)

        fax = FaxCommunication.objects.get(communication=self.comm)
        assert fax.fax_id == "98765"
        assert fax.to_number == self.comm.foia.fax

    def test_sends_attachments_ahead_of_the_message(self):
        FOIAFileFactory(
            comm=self.comm,
            ffile=ContentFile(b"%PDF-1.4 first", name="first.pdf"),
        )
        FOIAFileFactory(
            comm=self.comm,
            ffile=ContentFile(b"%PDF-1.4 second", name="second.pdf"),
        )
        with FakeApi("api.phaxio.com") as phaxio:
            phaxio.respond(phaxio_sent())
            send_fax(self.comm.pk, "Subject", "Body", 0)

        parts = file_parts(phaxio.requests[0])
        assert sorted(payload for _, _, payload in parts[:2]) == [
            b"%PDF-1.4 first",
            b"%PDF-1.4 second",
        ]
        assert all(filename.endswith(".pdf") for _, filename, _ in parts[:2])
        assert parts[2][2] == b"Body"

    def test_passes_test_fail_through_to_phaxio(self):
        with FakeApi("api.phaxio.com") as phaxio:
            phaxio.respond(phaxio_sent())
            send_fax(self.comm.pk, "Subject", "Body", 0, test_fail="busy")

        assert phaxio.requests[0].params["test_fail"] == "busy"

    def test_raises_and_records_no_fax_id_when_phaxio_rejects_the_fax(self):
        with FakeApi("api.phaxio.com") as phaxio:
            phaxio.respond(
                {"success": False, "message": "Invalid phone number"}, status=422
            )
            with self.assertRaises(Exception):
                send_fax(self.comm.pk, "Subject", "Body", 0)

        fax = FaxCommunication.objects.get(communication=self.comm)
        assert fax.fax_id == ""

    @patch("muckrock.foia.tasks.send_fax.retry", side_effect=Retry())
    def test_retries_without_calling_phaxio_when_the_request_has_no_fax_number(
        self, mock_retry
    ):
        self.comm.foia.fax = None
        self.comm.foia.save()
        with FakeApi("api.phaxio.com") as phaxio:
            with self.assertRaises(Retry):
                send_fax(self.comm.pk, "Subject", "Body", 0)

        mock_retry.assert_called_once()
        assert not phaxio.requests
