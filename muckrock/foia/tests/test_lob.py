"""
Tests for sending mail and checks through Lob, and for Lob's webhook
"""

# Django
from celery.exceptions import Retry
from django.test import TestCase, override_settings
from django.urls import reverse

# Standard Library
import hashlib
import hmac
import json
import time
from unittest.mock import Mock, patch

# Third Party
from constance.test import override_config
from lob_python import ApiClient, ApiException
from lob_python.api.checks_api import ChecksApi
from lob_python.api.letters_api import LettersApi
from lob_python.exceptions import ServiceException

# MuckRock
from muckrock.communication.models import Address, Check, MailCommunication
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory
from muckrock.foia.tasks import prepare_snail_mail
from muckrock.task.models import FlaggedTask, SnailMailTask


def lob_response(body, status=200):
    """A raw HTTP response from Lob, as lob-python returns it"""
    return Mock(
        status=status,
        reason="OK" if status == 200 else "Error",
        data=json.dumps(body).encode("utf8"),
        getheaders=dict,
    )


def lob_error(message, status=422, exc_class=ApiException):
    """The exception lob-python raises for an error response from Lob"""
    body = {"error": {"message": message, "status_code": status}}
    return exc_class(http_resp=lob_response(body, status))


def sent(mock_api_method):
    """The request body lob-python would send for the one call made"""
    mock_api_method.assert_called_once()
    model = mock_api_method.call_args.args[1]
    return ApiClient().sanitize_for_serialization(model)


@override_settings(LOB_SECRET_KEY="test_key", LOB_BANK_ACCOUNT_ID="bank_123")
@override_config(AUTO_LOB=True, AUTO_LOB_APPEAL=True, AUTO_LOB_PAY=True)
class PrepareSnailMailTests(TestCase):
    """Sending a communication by mail through Lob"""

    def setUp(self):
        UserFactory(username="MuckrockStaff")
        self.address = Address.objects.create(
            street="1 Main St", city="Boston", state="MA", zip_code="02108"
        )
        self.foia = FOIARequestFactory(
            agency__name="Boston Police Department", address=self.address
        )
        self.comm = FOIACommunicationFactory(
            foia=self.foia, category="n", communication="Please send the records."
        )

    def payment_comm(self):
        self.foia.agency.agencyaddress_set.create(
            address=self.address, request_type="check"
        )
        self.comm.category = "p"
        self.comm.save()
        return self.comm

    @patch.object(LettersApi, "create", autospec=True)
    def test_sends_a_letter_linking_to_the_stored_pdf(self, create):
        create.return_value = lob_response({"id": "ltr_abc123"})
        prepare_snail_mail(self.comm.pk, False, {}, None)

        mail = MailCommunication.objects.get(communication=self.comm)
        params = sent(create)
        assert params["file"] == mail.pdf.url
        assert params["use_type"] == "operational"
        assert params["description"] == f"Letter for communication {self.comm.pk}"
        assert params["to"]["name"] == "Boston Police Department"
        assert params["to"]["address_line1"] == "1 Main St"
        assert params["from"]["company"] == f"DEPT MR {self.foia.pk}"
        assert params["color"] is False
        assert params["double_sided"] is True
        assert params["metadata"] == {"mail_id": str(mail.pk)}
        assert params.get("extra_service") is None
        assert mail.lob_id == "ltr_abc123"
        self.foia.refresh_from_db()
        assert self.foia.status == "ack"
        assert not SnailMailTask.objects.exists()

    @patch.object(LettersApi, "create", autospec=True)
    def test_sends_a_certified_letter(self, create):
        create.return_value = lob_response({"id": "ltr_abc123"})
        prepare_snail_mail(self.comm.pk, False, {}, "certified")

        assert sent(create)["extra_service"] == "certified"

    @patch.object(ChecksApi, "create", autospec=True)
    def test_sends_a_check_with_the_stored_pdf_attached(self, create):
        comm = self.payment_comm()
        self.foia.add_tracking_id("ABC-123")
        create.return_value = lob_response({"id": "chk_abc123", "check_number": 10062})
        prepare_snail_mail(comm.pk, False, {"amount": "25.00"}, None)

        mail = MailCommunication.objects.get(communication=comm)
        params = sent(create)
        assert params["attachment"] == mail.pdf.url
        assert params["use_type"] == "operational"
        assert params["bank_account"] == "bank_123"
        assert params["amount"] == 25.0
        assert params["memo"] == f"MR {self.foia.pk} / ABC-123"
        assert params["metadata"] == {"mail_id": str(mail.pk)}
        assert mail.lob_id == "chk_abc123"
        check = Check.objects.get(communication=comm)
        assert check.number == 10062
        assert check.amount == 25

    @patch.object(LettersApi, "create", autospec=True)
    def test_files_a_snail_mail_task_with_lobs_error_when_lob_rejects_the_letter(
        self, create
    ):
        create.side_effect = lob_error("address_zip is invalid")
        prepare_snail_mail(self.comm.pk, False, {}, None)

        task = SnailMailTask.objects.get(communication=self.comm)
        assert task.reason == "lob"
        assert task.error_msg == "address_zip is invalid"
        assert MailCommunication.objects.get(communication=self.comm).lob_id == ""

    @patch("muckrock.foia.tasks.prepare_snail_mail.retry", side_effect=Retry())
    @patch.object(LettersApi, "create", autospec=True)
    def test_retries_when_lob_times_out(self, create, mock_retry):
        create.side_effect = lob_error(
            "Gateway Timeout", status=504, exc_class=ServiceException
        )
        with self.assertRaises(Retry):
            prepare_snail_mail(self.comm.pk, False, {}, None)

        mock_retry.assert_called_once()
        assert not SnailMailTask.objects.exists()


def signed_post(client, payload, key="secret"):
    """Post a webhook event signed the way Lob signs it"""
    body = json.dumps(payload).encode("utf8")
    timestamp = str(int(time.time()))
    signature = hmac.new(
        key.encode("utf8"), timestamp.encode("utf8") + b"." + body, hashlib.sha256
    ).hexdigest()
    return client.post(
        reverse("lob-webhook"),
        data=body,
        content_type="application/json",
        HTTP_LOB_SIGNATURE=signature,
        HTTP_LOB_SIGNATURE_TIMESTAMP=timestamp,
    )


@override_settings(LOB_SECRET_KEY="test_key", LOB_WEBHOOK_KEY="secret")
class LobWebhookTests(TestCase):
    """Lob's webhook for mail and check events"""

    @patch.object(ChecksApi, "get", autospec=True)
    def test_flags_the_request_when_a_check_fails(self, get):
        comm = FOIACommunicationFactory()
        mail = MailCommunication.objects.create(
            communication=comm, sent_datetime=comm.datetime
        )
        get.return_value = lob_response(
            {"id": "chk_534f10783683daa0", "metadata": {"mail_id": str(mail.pk)}}
        )
        payload = {
            "event_type": {"id": "check.failed"},
            "reference_id": "chk_534f10783683daa0",
            "body": {},
        }
        response = signed_post(self.client, payload)

        assert response.status_code == 200
        assert get.call_args.args[1] == "chk_534f10783683daa0"
        task = FlaggedTask.objects.get(foia=comm.foia)
        assert task.category == "payment"
        assert "https://dashboard.lob.com/checks/chk_534f10783683daa0" in task.text
