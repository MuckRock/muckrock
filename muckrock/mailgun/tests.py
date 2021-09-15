"""
Tests for mailgun
"""

# Django
from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Standard Library
import hashlib
import hmac
import os
import time
from datetime import date, datetime
from io import StringIO

# Third Party
import nose.tools
import pytz
import requests_mock
from freezegun import freeze_time

# MuckRock
from muckrock.communication.models import EmailAddress, EmailError, EmailOpen
from muckrock.core.test_utils import RunCommitHooksMixin
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory
from muckrock.foia.models import FOIACommunication
from muckrock.mailgun.views import bounces, delivered, opened, route_mailgun
from muckrock.task.models import OrphanTask


class TestMailgunViews(TestCase):
    """Shared methods for testing mailgun views"""

    def sign(self, data):
        """Add mailgun signature to data"""
        token = "token"
        timestamp = int(time.time())
        signature = hmac.new(
            key=settings.MAILGUN_ACCESS_KEY.encode("utf8"),
            msg="{}{}".format(timestamp, token).encode("utf8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        data["token"] = token
        data["timestamp"] = timestamp
        data["signature"] = signature

    def mailgun_route(
        self,
        from_="from@agency.gov",
        to_="example@requests.muckrock.com",
        subject="Test Subject",
        text="Test Text",
        signature="-John Doe",
        body=None,
        attachments=None,
        sign=True,
    ):
        """Helper function for testing the mailgun route"""
        # pylint: disable=too-many-arguments
        if attachments is None:
            attachments = []
        data = {
            "From": from_,
            "To": to_,
            "subject": subject,
            "stripped-text": text,
            "stripped-signature": signature,
            "body-plain": body or "%s\n%s" % (text, signature),
            "Message-ID": "message_id",
        }
        for i, attachment in enumerate(attachments):
            data["attachment-%d" % (i + 1)] = attachment
        if sign:
            self.sign(data)
        request = self.factory.post(reverse("mailgun-route"), data)
        return route_mailgun(request)


class TestMailgunViewHandleRequest(RunCommitHooksMixin, TestMailgunViews):
    """Tests for _handle_request"""

    def setUp(self):
        """Set up tests"""
        self.factory = RequestFactory()
        mail.outbox = []

    @requests_mock.Mocker()
    def test_normal(self, mock_requests):
        """Test a normal succesful response"""
        url = "https://www.example.com/raw_email/"
        mock_requests.get(
            settings.MAILGUN_API_URL + "/events",
            json={"items": [{"storage": {"url": url}}]},
        )
        mock_requests.get(url, json={"body-mime": "Raw email"})

        foia = FOIARequestFactory(status="ack")
        from_name = "Smith, Bob"
        from_email = "test@agency.gov"
        from_ = '"%s" <%s>' % (from_name, from_email)
        to_ = '%s, "Doe, John" <other@agency.gov>' % foia.get_request_email()
        subject = "Test subject"
        text = "Test normal."
        signature = "-Charlie Jones"

        self.mailgun_route(from_, to_, subject, text, signature)
        foia.refresh_from_db()

        last_comm = foia.communications.last()
        nose.tools.eq_(last_comm.communication, "%s\n%s" % (text, signature))
        nose.tools.eq_(last_comm.subject, subject)
        nose.tools.eq_(last_comm.from_user, foia.agency.get_user())
        nose.tools.eq_(last_comm.to_user, foia.user)
        nose.tools.eq_(last_comm.response, True)
        nose.tools.eq_(last_comm.full_html, False)
        self.run_commit_hooks()
        nose.tools.eq_(last_comm.get_raw_email().raw_email, "Raw email")
        nose.tools.eq_(last_comm.responsetask_set.count(), 1)
        nose.tools.eq_(foia.email, EmailAddress.objects.fetch(from_email))
        nose.tools.eq_(
            set(foia.cc_emails.all()),
            set(EmailAddress.objects.fetch_many("other@agency.gov")),
        )
        nose.tools.eq_(foia.status, "processed")

    def test_bad_sender(self):
        """Test receiving a message from an unauthorized sender"""

        foia = FOIARequestFactory()
        from_ = "test@agency.com"
        to_ = foia.get_request_email()
        text = "Test bad sender."
        signature = "-Spammer"
        self.mailgun_route(from_, to_, text=text, signature=signature)

        communication = FOIACommunication.objects.get(likely_foia=foia)
        nose.tools.eq_(communication.communication, "%s\n%s" % (text, signature))
        nose.tools.ok_(
            OrphanTask.objects.filter(
                communication=communication,
                reason="bs",
                address=foia.get_request_email().split("@")[0],
            ).exists()
        )

    def test_block_incoming(self):
        """Test receiving a message from an unauthorized sender"""

        foia = FOIARequestFactory(block_incoming=True)
        to_ = foia.get_request_email()
        text = "Test block incoming."
        signature = "-Too Late"
        self.mailgun_route(to_=to_, text=text, signature=signature)

        communication = FOIACommunication.objects.get(likely_foia=foia)
        nose.tools.eq_(communication.communication, "%s\n%s" % (text, signature))
        nose.tools.ok_(
            OrphanTask.objects.filter(
                communication=communication,
                reason="ib",
                address=foia.get_request_email().split("@")[0],
            ).exists()
        )

    def test_bad_addr(self):
        """Test sending to a non existent FOIA request"""

        to_ = "123-12345678@requests.muckrock.com"
        text = "Test bad address."
        self.mailgun_route(to_=to_, text=text)

        nose.tools.ok_(
            OrphanTask.objects.filter(reason="ia", address="123-12345678").exists()
        )

    def test_attachments(self):
        """Test a message with an attachment"""
        try:
            foia = FOIARequestFactory()
            to_ = foia.get_request_email()
            attachments = [StringIO("Good file"), StringIO("Ignore File")]
            attachments[0].name = "data.pdf"
            attachments[1].name = "ignore.p7s"
            self.mailgun_route(to_=to_, attachments=attachments)
            foia.refresh_from_db()
            file_path = date.today().strftime("foia_files/%Y/%m/%d/data.pdf")
            nose.tools.eq_(foia.get_files().count(), 1)
            nose.tools.eq_(foia.get_files().first().ffile.name, file_path)
        finally:
            foia.communications.first().files.first().delete()
            file_path = os.path.join(settings.SITE_ROOT, "static/media/", file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_bad_strip(self):
        """Test an improperly stripped message"""

        foia = FOIARequestFactory()
        to_ = foia.get_request_email()
        text = ""
        body = "Here is the full body."
        self.mailgun_route(to_=to_, text=text, body=body)

        last_comm = foia.communications.last()
        nose.tools.eq_(last_comm.communication, body)

    def test_bad_verify(self):
        """Test an improperly signed message"""

        foia = FOIARequestFactory(block_incoming=True)
        to_ = foia.get_request_email()
        response = self.mailgun_route(to_=to_, sign=False)
        nose.tools.eq_(response.status_code, 403)

    def test_deleted(self):
        """Test a message to a deleted request"""

        foia = FOIARequestFactory(status="abandoned", deleted=True)
        from_name = "Smith, Bob"
        from_email = "test@agency.gov"
        from_ = '"%s" <%s>' % (from_name, from_email)
        to_ = foia.get_request_email()
        subject = "Test subject"
        text = "Test normal."
        signature = "-Charlie Jones"

        self.mailgun_route(from_, to_, subject, text, signature)
        foia.refresh_from_db()

        # no communication should be created, and an autoreply sould be mailed out
        nose.tools.eq_(foia.communications.count(), 0)
        nose.tools.eq_(
            mail.outbox[0].body, render_to_string("text/foia/deleted_autoreply.txt")
        )
        nose.tools.eq_(mail.outbox[0].to, [from_])


class TestMailgunViewCatchAll(TestMailgunViews):
    """Tests for catch all"""

    def setUp(self):
        """Set up tests"""
        self.factory = RequestFactory()

    def test_catchall(self):
        """Test catching an orphan"""

        to_ = "foobar@requests.muckrock.com"
        text = "Test catch all orphan."
        signature = "-Clumsy Typer"

        self.mailgun_route(to_=to_, text=text, signature=signature)

        task = OrphanTask.objects.get(
            reason="ia", address="foobar@requests.muckrock.com"
        )
        nose.tools.eq_(task.communication.communication, "%s\n%s" % (text, signature))


@freeze_time("2017-01-02 12:00:00 EST", tz_offset=-5)
class TestMailgunViewWebHooks(TestMailgunViews):
    """Tests for mailgun webhooks"""

    def setUp(self):
        """Set up tests"""
        self.factory = RequestFactory()

    def test_bounce(self):
        """Test a bounce webhook"""

        recipient = "alice@example.com"
        comm = FOIACommunicationFactory(
            foia__email=EmailAddress.objects.fetch(recipient), foia__agency__fax=None
        )
        email = comm.emails.first()
        event = "bounced"
        code = 550
        error = (
            "5.1.1 The email account that you tried to reach "
            "does not exist. Please try 5.1.1 double-checking "
            "the recipient's email address for typos or 5.1.1 "
            "unnecessary spaces. Learn more at 5.1.1 "
            "http://support.example.com/mail/bin/answer.py"
        )
        data = {
            "event": event,
            "email_id": email.pk,
            "code": code,
            "error": error,
            "recipient": recipient,
        }
        self.sign(data)
        request = self.factory.post(reverse("mailgun-bounces"), data)
        bounces(request)  # pylint: disable=no-value-for-parameter
        comm.refresh_from_db()

        nose.tools.ok_(
            EmailError.objects.filter(
                email=email,
                datetime=datetime(2017, 1, 2, 17, tzinfo=pytz.utc),
                recipient=EmailAddress.objects.fetch(recipient),
                code=code,
                error=error,
                event=event,
            ).exists()
        )

    def test_open(self):
        """Test an open webhook"""
        # pylint: disable=too-many-locals

        recipient = "alice@example.com"
        comm = FOIACommunicationFactory(
            foia__email=EmailAddress.objects.fetch(recipient)
        )
        email = comm.emails.first()
        event = "opened"
        city = "Boston"
        region = "MA"
        country = "US"
        client_type = "browser"
        client_name = "Chrome"
        client_os = "Linux"
        device_type = "desktop"
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 "
            "(KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31"
        )
        ip_address = "50.56.129.169"
        data = {
            "event": event,
            "email_id": email.pk,
            "recipient": recipient,
            "city": city,
            "region": region,
            "country": country,
            "client-type": client_type,
            "client-name": client_name,
            "client-os": client_os,
            "device-type": device_type,
            "user-agent": user_agent,
            "ip": ip_address,
        }
        self.sign(data)
        request = self.factory.post(reverse("mailgun-opened"), data)
        opened(request)  # pylint: disable=no-value-for-parameter
        comm.refresh_from_db()

        nose.tools.ok_(
            EmailOpen.objects.filter(
                email=email,
                datetime=datetime(2017, 1, 2, 17, tzinfo=pytz.utc),
                recipient=EmailAddress.objects.fetch(recipient),
                city=city,
                region=region,
                country=country,
                client_type=client_type,
                client_name=client_name,
                client_os=client_os,
                device_type=device_type,
                user_agent=user_agent[:255],
                ip_address=ip_address,
            ).exists()
        )

    def test_delivered(self):
        """Test a delivered webhook"""

        comm = FOIACommunicationFactory()
        email = comm.emails.first()
        data = {"event": "delivered", "email_id": email.pk}
        self.sign(data)
        request = self.factory.post(reverse("mailgun-delivered"), data)
        delivered(request)  # pylint: disable=no-value-for-parameter
        comm.refresh_from_db()

        nose.tools.eq_(
            comm.emails.first().confirmed_datetime,
            datetime(2017, 1, 2, 17, tzinfo=pytz.utc),
        )
