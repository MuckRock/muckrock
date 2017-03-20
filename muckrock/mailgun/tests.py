"""
Tests for mailgun
"""

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from datetime import date, datetime
from freezegun import freeze_time
from StringIO import StringIO
import hashlib
import hmac
import nose.tools
import os
import time

from muckrock.foia.models import (
        FOIACommunication,
        CommunicationError,
        CommunicationOpen,
        )
from muckrock.factories import FOIARequestFactory, FOIACommunicationFactory
from muckrock.mailgun.views import (
        route_mailgun,
        bounces,
        opened,
        delivered,
        _allowed_email,
        )
from muckrock.mailgun.models import WhitelistDomain
from muckrock.task.models import OrphanTask, FailedFaxTask, RejectedEmailTask

# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods


class TestMailgunViews(TestCase):
    """Shared methods for testing mailgun views"""

    def sign(self, data):
        """Add mailgun signature to data"""
        token = 'token'
        timestamp = int(time.time())
        signature = hmac.new(
                key=settings.MAILGUN_ACCESS_KEY,
                msg='%s%s' % (timestamp, token),
                digestmod=hashlib.sha256).hexdigest()
        data['token'] = token
        data['timestamp'] = timestamp
        data['signature'] = signature

    def mailgun_route(self,
            from_='from@agency.gov',
            to_='example@requests.muckrock.com',
            subject='Test Subject',
            text='Test Text',
            signature='-John Doe',
            body=None,
            attachments=None,
            sign=True,
            ):
        """Helper function for testing the mailgun route"""
        # pylint: disable=too-many-arguments
        if attachments is None:
            attachments = []
        data = {
            'From': from_,
            'To': to_,
            'subject': subject,
            'stripped-text': text,
            'stripped-signature': signature,
            'body-plain': body or '%s\n%s' % (text, signature),
        }
        for i, attachment in enumerate(attachments):
            data['attachment-%d' % (i + 1)] = attachment
        if sign:
            self.sign(data)
        request = self.factory.post(reverse('mailgun-route'), data)
        return route_mailgun(request)


class TestMailgunViewHandleRequest(TestMailgunViews):
    """Tests for _handle_request"""

    def setUp(self):
        """Set up tests"""
        self.factory = RequestFactory()

    def test_normal(self):
        """Test a normal succesful response"""

        foia = FOIARequestFactory(status='ack')
        from_name = 'Smith, Bob'
        from_email = 'test@agency.gov'
        from_ = '"%s" <%s>' % (from_name, from_email)
        to_ = ('%s@requests.muckrock.com, "Doe, John" <other@agency.gov>' %
                foia.get_mail_id())
        subject = 'Test subject'
        text = 'Test normal.'
        signature = '-Charlie Jones'

        self.mailgun_route(from_, to_, subject, text, signature)
        foia.refresh_from_db()

        last_comm = foia.communications.last()
        nose.tools.eq_(last_comm.communication, '%s\n%s' % (text, signature))
        nose.tools.eq_(last_comm.subject, subject)
        nose.tools.eq_(last_comm.from_who, from_name)
        nose.tools.eq_(last_comm.priv_from_who, from_)
        nose.tools.eq_(last_comm.to_who, foia.user.get_full_name())
        nose.tools.eq_(last_comm.priv_to_who, to_)
        nose.tools.eq_(last_comm.response, True)
        nose.tools.eq_(last_comm.full_html, False)
        nose.tools.eq_(last_comm.delivered, 'email')
        nose.tools.ok_(last_comm.rawemail)
        nose.tools.eq_(last_comm.responsetask_set.count(), 1)
        nose.tools.eq_(foia.email, from_email)
        nose.tools.eq_(foia.other_emails, 'other@agency.gov')
        nose.tools.eq_(foia.status, 'processed')

    def test_bad_sender(self):
        """Test receiving a message from an unauthorized sender"""

        foia = FOIARequestFactory()
        from_ = 'test@agency.com'
        to_ = '%s@requests.muckrock.com' % foia.get_mail_id()
        text = 'Test bad sender.'
        signature = '-Spammer'
        self.mailgun_route(from_, to_, text=text, signature=signature)

        communication = FOIACommunication.objects.get(likely_foia=foia)
        nose.tools.eq_(communication.communication, '%s\n%s' % (text, signature))
        nose.tools.ok_(OrphanTask.objects
                .filter(
                    communication=communication,
                    reason='bs',
                    address=foia.get_mail_id(),
                    )
                .exists()
                )

    def test_block_incoming(self):
        """Test receiving a message from an unauthorized sender"""

        foia = FOIARequestFactory(block_incoming=True)
        to_ = '%s@requests.muckrock.com' % foia.get_mail_id()
        text = 'Test block incoming.'
        signature = '-Too Late'
        self.mailgun_route(to_=to_, text=text, signature=signature)

        communication = FOIACommunication.objects.get(likely_foia=foia)
        nose.tools.eq_(communication.communication, '%s\n%s' % (text, signature))
        nose.tools.ok_(OrphanTask.objects
                .filter(
                    communication=communication,
                    reason='ib',
                    address=foia.get_mail_id(),
                    )
                .exists()
                )

    def test_bad_addr(self):
        """Test sending to a non existent FOIA request"""

        to_ = '123-12345678@requests.muckrock.com'
        text = 'Test bad address.'
        self.mailgun_route(to_=to_, text=text)

        nose.tools.ok_(OrphanTask.objects
                .filter(
                    reason='ia',
                    address='123-12345678'
                    )
                .exists()
                )

    def test_attachments(self):
        """Test a message with an attachment"""

        try:
            foia = FOIARequestFactory()
            to_ = '%s@requests.muckrock.com' % foia.get_mail_id()
            attachments = [StringIO('Good file'), StringIO('Ignore File')]
            attachments[0].name = 'data.pdf'
            attachments[1].name = 'ignore.p7s'
            self.mailgun_route(to_=to_, attachments=attachments)
            foia.refresh_from_db()
            file_path = date.today().strftime('foia_files/%Y/%m/%d/data.pdf')
            nose.tools.eq_(foia.files.count(), 1)
            nose.tools.eq_(foia.files.first().ffile.name, file_path)

        finally:
            foia.files.first().delete()
            file_path = os.path.join(settings.SITE_ROOT, 'static/media/', file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_bad_strip(self):
        """Test an improperly stripped message"""

        foia = FOIARequestFactory()
        to_ = '%s@requests.muckrock.com' % foia.get_mail_id()
        text = ''
        body = 'Here is the full body.'
        self.mailgun_route(to_=to_, text=text, body=body)

        last_comm = foia.communications.last()
        nose.tools.eq_(last_comm.communication, body)

    def test_bad_verify(self):
        """Test an improperly signed message"""

        foia = FOIARequestFactory(block_incoming=True)
        to_ = '%s@requests.muckrock.com' % foia.get_mail_id()
        response = self.mailgun_route(to_=to_, sign=False)
        nose.tools.eq_(response.status_code, 403)


class TestMailgunViewCatchAll(TestMailgunViews):
    """Tests for catch all"""

    def setUp(self):
        """Set up tests"""
        self.factory = RequestFactory()

    def test_catchall(self):
        """Test catching an orphan"""

        to_ = 'foobar@requests.muckrock.com'
        text = 'Test catch all orphan.'
        signature = '-Clumsy Typer'

        self.mailgun_route(to_=to_, text=text, signature=signature)

        task = OrphanTask.objects.get(
                reason='ia',
                address='foobar@requests.muckrock.com',
                )
        nose.tools.eq_(
                task.communication.communication,
                '%s\n%s' % (text, signature),
                )


@freeze_time("2017-01-02 12:00:00 EST", tz_offset=-5)
class TestMailgunViewWebHooks(TestMailgunViews):
    """Tests for mailgun webhooks"""

    def setUp(self):
        """Set up tests"""
        self.factory = RequestFactory()

    def test_bounce(self):
        """Test a bounce webhook"""

        comm = FOIACommunicationFactory()
        event = 'bounced'
        code = 550
        error = ("5.1.1 The email account that you tried to reach "
                "does not exist. Please try 5.1.1 double-checking "
                "the recipient's email address for typos or 5.1.1 "
                "unnecessary spaces. Learn more at 5.1.1 "
                "http://support.example.com/mail/bin/answer.py")
        recipient = 'alice@example.com'
        data = {
                'event': event,
                'comm_id': comm.pk,
                'code': code,
                'error': error,
                'recipient': recipient,
                }
        self.sign(data)
        request = self.factory.post(reverse('mailgun-bounces'), data)
        bounces(request) # pylint: disable=no-value-for-parameter
        comm.refresh_from_db()

        nose.tools.ok_(RejectedEmailTask.objects
                .filter(
                    category='b',
                    foia=comm.foia,
                    email=recipient,
                    error=error,
                    )
                .exists()
                )

        nose.tools.ok_(CommunicationError.objects
                .filter(
                    communication=comm,
                    date=datetime(2017, 1, 2, 12),
                    recipient=recipient,
                    code=code,
                    error=error,
                    event=event,
                    )
                .exists()
                )

    def test_open(self):
        """Test an open webhook"""

        comm = FOIACommunicationFactory()
        event = 'opened'
        recipient = 'alice@example.com'
        city = 'Boston'
        region = 'MA'
        country = 'US'
        client_type = 'browser'
        client_name = 'Chrome'
        client_os = 'Linux'
        device_type = 'desktop'
        user_agent = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.31 '
                      '(KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31')
        ip_address = '50.56.129.169'
        data = {
                'event': event,
                'comm_id': comm.pk,
                'recipient': recipient,
                'city': city,
                'region': region,
                'country': country,
                'client-type': client_type,
                'client-name': client_name,
                'client-os': client_os,
                'device-type': device_type,
                'user-agent': user_agent,
                'ip': ip_address,
                }
        self.sign(data)
        request = self.factory.post(reverse('mailgun-opened'), data)
        opened(request) # pylint: disable=no-value-for-parameter
        comm.refresh_from_db()

        nose.tools.ok_(CommunicationOpen.objects
                .filter(
                    communication=comm,
                    date=datetime(2017, 1, 2, 12),
                    recipient=recipient,
                    city=city,
                    region=region,
                    country=country,
                    client_type=client_type,
                    client_name=client_name,
                    client_os=client_os,
                    device_type=device_type,
                    user_agent=user_agent[:255],
                    ip_address=ip_address,
                    )
                .exists()
                )

    def test_delivered(self):
        """Test a delivered webhook"""

        comm = FOIACommunicationFactory(confirmed=None)
        data = {
                'event': 'delivered',
                'comm_id': comm.pk,
                }
        self.sign(data)
        request = self.factory.post(reverse('mailgun-delivered'), data)
        delivered(request) # pylint: disable=no-value-for-parameter
        comm.refresh_from_db()

        nose.tools.eq_(comm.confirmed, datetime(2017, 1, 2, 12))


class TestHelperFunctions(TestCase):
    """Tests view helper functions"""

    def test_allowed_email(self):
        """Test allowed email function"""
        foia = FOIARequestFactory(
                email='foo@bar.com',
                other_emails='foo@baz.com',
                agency__email='main@agency.com',
                agency__other_emails='foo@agency.com',
                )
        WhitelistDomain.objects.create(domain='whitehat.edu')

        allowed_emails = [
                'bar@bar.com', # same domain
                'BAR@BAR.COM', # case insensitive
                'foo@baz.com', # other email
                'foo@agency.com', # agency email
                'any@usa.gov', # any government tld
                'any@domain.ma.us', # any government tld
                'foo@whitehat.edu', # white listed domain
                ]
        not_allowed_emails = [
                'other@baz.com',
                'other@agency.com',
                'random@random.edu',
                'foo@co.uk',
                ]
        for email in allowed_emails:
            nose.tools.ok_(_allowed_email(email, foia))
        for email in not_allowed_emails:
            nose.tools.assert_false(_allowed_email(email, foia))
        # non foia test - any agency email
        nose.tools.ok_(_allowed_email('main@agency.com'))
