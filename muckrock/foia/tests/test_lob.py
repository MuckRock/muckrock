"""
Tests for sending mail and checks through Lob, and for Lob's webhook

Lob is faked at the HTTP connection pool, below any Lob client library, so these
tests pin down what goes over the wire rather than how the client is called.
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
from email.parser import BytesParser
from email.policy import HTTP
from io import BytesIO
from unittest.mock import patch
from urllib.parse import parse_qsl, urlsplit

# Third Party
from constance.test import override_config
from urllib3 import HTTPResponse
from urllib3.connectionpool import HTTPConnectionPool

# MuckRock
from muckrock.communication.models import Address, Check, MailCommunication
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory
from muckrock.foia.tasks import prepare_snail_mail
from muckrock.task.models import FlaggedTask, SnailMailTask

LOB_TIMESTAMP = "2026-11-16T18:00:00.000Z"


def lob_address(**kwargs):
    """An address object as Lob returns it"""
    return {
        "id": "adr_d3489cd64c791ab5",
        "name": "Agency",
        "address_line1": "1 Main St",
        "address_city": "Boston",
        "address_state": "MA",
        "address_zip": "02108",
        "address_country": "UNITED STATES",
        "date_created": LOB_TIMESTAMP,
        "date_modified": LOB_TIMESTAMP,
        "object": "address",
        **kwargs,
    }


def lob_letter(**kwargs):
    """A letter object as Lob returns it"""
    return {
        "id": "ltr_4868c3b754655f90",
        "description": "Letter",
        "metadata": {},
        "to": lob_address(),
        "from": lob_address(id="adr_210a8d4b0b76d77b", name="MuckRock News"),
        "color": False,
        "double_sided": True,
        "address_placement": "top_first_page",
        "return_envelope": False,
        "extra_service": None,
        "mail_type": "usps_first_class",
        "url": "https://lob-assets.com/letters/ltr_4868c3b754655f90.pdf",
        "carrier": "USPS",
        "tracking_events": [],
        "thumbnails": [],
        "expected_delivery_date": "2026-11-23",
        "send_date": LOB_TIMESTAMP,
        "date_created": LOB_TIMESTAMP,
        "date_modified": LOB_TIMESTAMP,
        "use_type": "operational",
        "object": "letter",
        **kwargs,
    }


def lob_check(**kwargs):
    """A check object as Lob returns it"""
    return {
        "id": "chk_534f10783683daa0",
        "description": "Check",
        "metadata": {},
        "check_number": 10062,
        "memo": "",
        "amount": 25.0,
        "url": "https://lob-assets.com/checks/chk_534f10783683daa0.pdf",
        "to": lob_address(),
        "from": lob_address(id="adr_210a8d4b0b76d77b", name="MuckRock News"),
        "bank_account": {
            "id": "bank_8cad8df5354d33f",
            "description": "Test Bank Account",
            "routing_number": "322271627",
            "account_number": "123456789",
            "account_type": "company",
            "signatory": "MuckRock",
            "bank_name": "J.P. MORGAN CHASE BANK, N.A.",
            "verified": True,
            "date_created": LOB_TIMESTAMP,
            "date_modified": LOB_TIMESTAMP,
            "object": "bank_account",
        },
        "carrier": "USPS",
        "tracking_events": [],
        "thumbnails": [],
        "expected_delivery_date": "2026-11-23",
        "mail_type": "usps_first_class",
        "send_date": LOB_TIMESTAMP,
        "date_created": LOB_TIMESTAMP,
        "date_modified": LOB_TIMESTAMP,
        "use_type": "operational",
        "object": "check",
        **kwargs,
    }


def lob_error(message, status_code=422):
    """An error body as Lob returns it"""
    return {"error": {"message": message, "status_code": status_code}}


def _nest(flat):
    """Turn form keys like `to[name]` into nested dicts"""
    nested = {}
    for key, value in flat.items():
        if "[" in key:
            outer, inner = key.rstrip("]").split("[", 1)
            nested.setdefault(outer, {})[inner] = value
        else:
            nested[key] = value
    return nested


def _scalar(value):
    if isinstance(value, dict):
        return {k: _scalar(v) for k, v in value.items() if v is not None}
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, bytes):
        return value
    return str(value).lower() if str(value) in ("True", "False") else str(value)


class LobRequest:
    """A request sent to Lob, with its parameters decoded from any body encoding"""

    def __init__(self, method, url, headers, body):
        self.method = method
        self.path = urlsplit(url).path
        self.headers = headers or {}
        if isinstance(body, str):
            body = body.encode("utf8")
        self.params = self._decode(body or b"")

    def _decode(self, body):
        content_type = next(
            (v for k, v in self.headers.items() if k.lower() == "content-type"), ""
        )
        if content_type.startswith("multipart/form-data"):
            message = BytesParser(policy=HTTP).parsebytes(
                f"Content-Type: {content_type}\r\n\r\n".encode() + body
            )
            flat = {}
            for part in message.iter_parts():
                name = part.get_param("name", header="content-disposition")
                payload = part.get_payload(decode=True)
                flat[name] = payload if part.get_filename() else payload.decode("utf8")
            return _scalar(_nest(flat))
        if content_type.startswith("application/x-www-form-urlencoded"):
            return _scalar(_nest(dict(parse_qsl(body.decode("utf8")))))
        if body:
            return _scalar(json.loads(body))
        return {}


class FakeLob:
    """Stands in for api.lob.com, answering requests in the order queued"""

    def __init__(self):
        self.requests = []
        self._responses = []

    def respond(self, body, status=200):
        self._responses.append((status, body))

    def __enter__(self):
        self._patch = patch.object(
            HTTPConnectionPool, "urlopen", autospec=True, side_effect=self._urlopen
        )
        self._patch.start()
        return self

    def __exit__(self, *exc):
        self._patch.stop()

    def _urlopen(self, pool, method, url, body=None, headers=None, **kwargs):
        assert pool.host == "api.lob.com", f"unexpected request to {pool.host}"
        self.requests.append(LobRequest(method, url, headers, body))
        status, response = self._responses.pop(0)
        return HTTPResponse(
            body=BytesIO(json.dumps(response).encode("utf8")),
            headers={"Content-Type": "application/json"},
            status=status,
            reason="OK" if status == 200 else "Error",
            preload_content=False,
        )


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

    def test_sends_a_letter_to_the_agency_address(self):
        with FakeLob() as lob:
            lob.respond(lob_letter())
            prepare_snail_mail(self.comm.pk, False, {}, None)

        assert len(lob.requests) == 1
        request = lob.requests[0]
        assert request.method == "POST"
        assert request.path == "/v1/letters"
        mail = MailCommunication.objects.get(communication=self.comm)
        params = request.params
        assert params["description"] == f"Letter for communication {self.comm.pk}"
        assert params["to"] == {
            "name": "Boston Police Department",
            "company": "{} Office".format(
                self.foia.agency.jurisdiction.get_law_name(abbrev=True)
            ),
            "address_line1": "1 Main St",
            "address_city": "Boston",
            "address_state": "MA",
            "address_zip": "02108",
        }
        assert params["from"] == {
            "name": "MuckRock News",
            "company": f"DEPT MR {self.foia.pk}",
            "address_line1": "263 Huntington Ave",
            "address_city": "Boston",
            "address_state": "MA",
            "address_zip": "02115",
        }
        assert params["color"] == "false"
        assert params["double_sided"] == "true"
        assert params["metadata"] == {"mail_id": str(mail.pk)}
        assert "extra_service" not in params
        assert params["file"].startswith(b"%PDF")

    def test_records_the_lob_id_and_marks_the_request_sent(self):
        with FakeLob() as lob:
            lob.respond(lob_letter(id="ltr_abc123"))
            prepare_snail_mail(self.comm.pk, False, {}, None)

        mail = MailCommunication.objects.get(communication=self.comm)
        assert mail.lob_id == "ltr_abc123"
        self.foia.refresh_from_db()
        assert self.foia.status == "ack"
        assert not SnailMailTask.objects.exists()

    def test_sends_a_certified_letter(self):
        with FakeLob() as lob:
            lob.respond(lob_letter(extra_service="certified"))
            prepare_snail_mail(self.comm.pk, False, {}, "certified")

        assert lob.requests[0].params["extra_service"] == "certified"

    def test_sends_a_check_with_the_payment_letter_attached(self):
        comm = self.payment_comm()
        self.foia.add_tracking_id("ABC-123")
        with FakeLob() as lob:
            lob.respond(lob_check(id="chk_abc123", check_number=10062))
            prepare_snail_mail(comm.pk, False, {"amount": "25.00"}, None)

        request = lob.requests[0]
        assert request.method == "POST"
        assert request.path == "/v1/checks"
        mail = MailCommunication.objects.get(communication=comm)
        params = request.params
        assert params["description"] == f"Check for communication {comm.pk}"
        assert params["to"]["name"] == "Boston Police Department"
        assert params["from"]["company"] == f"DEPT MR {self.foia.pk}"
        assert params["bank_account"] == "bank_123"
        assert float(params["amount"]) == 25.0
        assert params["memo"] == f"MR {self.foia.pk} / ABC-123"
        assert params["metadata"] == {"mail_id": str(mail.pk)}
        assert params["attachment"].startswith(b"%PDF")

    def test_records_the_check_and_the_lob_id(self):
        comm = self.payment_comm()
        with FakeLob() as lob:
            lob.respond(lob_check(id="chk_abc123", check_number=10062))
            prepare_snail_mail(comm.pk, False, {"amount": "25.00"}, None)

        mail = MailCommunication.objects.get(communication=comm)
        assert mail.lob_id == "chk_abc123"
        check = Check.objects.get(communication=comm)
        assert check.number == 10062
        assert check.amount == 25
        assert check.agency == self.foia.agency

    def test_drops_the_tracking_id_from_a_memo_over_40_characters(self):
        comm = self.payment_comm()
        self.foia.add_tracking_id("X" * 40)
        with FakeLob() as lob:
            lob.respond(lob_check())
            prepare_snail_mail(comm.pk, False, {"amount": "25.00"}, None)

        assert lob.requests[0].params["memo"] == f"MR {self.foia.pk}"

    def test_files_a_snail_mail_task_with_lobs_error_when_lob_rejects_the_letter(
        self,
    ):
        with FakeLob() as lob:
            lob.respond(lob_error("address_zip is invalid"), status=422)
            prepare_snail_mail(self.comm.pk, False, {}, None)

        task = SnailMailTask.objects.get(communication=self.comm)
        assert task.reason == "lob"
        assert "address_zip is invalid" in task.error_msg
        assert MailCommunication.objects.get(communication=self.comm).lob_id == ""

    @patch("muckrock.foia.tasks.prepare_snail_mail.retry", side_effect=Retry())
    def test_retries_when_lob_times_out(self, mock_retry):
        with FakeLob() as lob:
            lob.respond(lob_error("Gateway Timeout", status_code=504), status=504)
            with self.assertRaises(Retry):
                prepare_snail_mail(self.comm.pk, False, {}, None)

        mock_retry.assert_called_once()
        assert not SnailMailTask.objects.exists()

    @override_config(AUTO_LOB=False)
    def test_files_a_snail_mail_task_without_calling_lob_when_auto_lob_is_off(self):
        with FakeLob() as lob:
            prepare_snail_mail(self.comm.pk, False, {}, None)

        assert not lob.requests
        assert SnailMailTask.objects.get(communication=self.comm).reason == "auto"

    @override_config(AUTO_LOB=False)
    def test_sends_through_lob_when_forced_with_auto_lob_off(self):
        with FakeLob() as lob:
            lob.respond(lob_letter())
            prepare_snail_mail(self.comm.pk, False, {}, None, force=True)

        assert len(lob.requests) == 1
        assert not SnailMailTask.objects.exists()

    def test_files_a_snail_mail_task_without_calling_lob_for_an_address_lob_rejects(
        self,
    ):
        self.address.street = "X" * 65
        self.address.save()
        with FakeLob() as lob:
            prepare_snail_mail(self.comm.pk, False, {}, None)

        assert not lob.requests
        assert SnailMailTask.objects.get(communication=self.comm).reason == "badadd"

    @override_settings(CHECK_LIMIT=200)
    def test_files_a_snail_mail_task_without_calling_lob_for_a_check_over_the_limit(
        self,
    ):
        comm = self.payment_comm()
        with FakeLob() as lob:
            prepare_snail_mail(comm.pk, False, {"amount": "250.00"}, None)

        assert not lob.requests
        assert SnailMailTask.objects.get(communication=comm).reason == "limit"


def signed_post(client, payload, key="secret", timestamp=None):
    """Post a webhook event signed the way Lob signs it"""
    body = json.dumps(payload).encode("utf8")
    timestamp = str(int(timestamp or time.time()))
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

    def setUp(self):
        self.comm = FOIACommunicationFactory()
        self.mail = MailCommunication.objects.create(
            communication=self.comm, sent_datetime=self.comm.datetime
        )

    def event(self, event_type, **kwargs):
        return {
            "id": "evt_9e84094c9368cfb2",
            "event_type": {"id": event_type, "object": "event_type"},
            "date_created": LOB_TIMESTAMP,
            "reference_id": "ltr_4868c3b754655f90",
            "body": lob_letter(metadata={"mail_id": str(self.mail.pk)}),
            "object": "event",
            **kwargs,
        }

    def test_records_a_delivery_event_on_the_mail(self):
        response = signed_post(self.client, self.event("letter.delivered"))

        assert response.status_code == 200
        event = self.mail.events.get()
        assert event.event == "letter.delivered"
        assert event.datetime.isoformat() == "2026-11-16T18:00:00+00:00"

    def test_rejects_an_event_with_a_bad_signature(self):
        response = signed_post(
            self.client, self.event("letter.delivered"), key="not the secret"
        )

        assert response.status_code == 403
        assert not self.mail.events.exists()

    def test_rejects_an_event_signed_more_than_five_minutes_ago(self):
        response = signed_post(
            self.client,
            self.event("letter.delivered"),
            timestamp=time.time() - 301,
        )

        assert response.status_code == 403

    def test_flags_the_request_when_a_check_fails(self):
        payload = self.event(
            "check.failed", reference_id="chk_534f10783683daa0", body={}
        )
        with FakeLob() as lob:
            lob.respond(lob_check(metadata={"mail_id": str(self.mail.pk)}))
            response = signed_post(self.client, payload)

        assert response.status_code == 200
        assert len(lob.requests) == 1
        assert lob.requests[0].method == "GET"
        assert lob.requests[0].path == "/v1/checks/chk_534f10783683daa0"
        task = FlaggedTask.objects.get(foia=self.comm.foia)
        assert task.category == "payment"
        assert "https://dashboard.lob.com/checks/chk_534f10783683daa0" in task.text

    def test_rejects_an_event_without_a_mail_id(self):
        payload = self.event("letter.delivered", body={})
        response = signed_post(self.client, payload)

        assert response.status_code == 400
