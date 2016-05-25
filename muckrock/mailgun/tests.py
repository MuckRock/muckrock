"""
Tests for mailgun
"""

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from datetime import date
import hashlib
import hmac
import nose.tools
import os
import time

from muckrock.foia.models import FOIARequest

# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

class TestMailgunViews(TestCase):
    """Tests for Mailgun views"""
    fixtures = ['holidays.json', 'agency_types.json', 'test_agencies.json', 'test_users.json',
                'test_profiles.json', 'jurisdictions.json', 'test_foiarequests.json']

    def setUp(self):
        """Set up tests"""
        mail.outbox = []
        self.kwargs = {"wsgi.url_scheme": "https"}

    def sign(self, data):
        """Add mailgun signature to data"""
        token = 'token'
        timestamp = int(time.time())
        signature = hmac.new(key=settings.MAILGUN_ACCESS_KEY,
                             msg='%s%s' % (timestamp, token),
                             digestmod=hashlib.sha256).hexdigest()
        data['token'] = token
        data['timestamp'] = timestamp
        data['signature'] = signature

    def test_normal(self):
        """Test a normal succesful response"""

        foia = FOIARequest.objects.get(pk=1)
        data = {
            'From': 'test@agency.gov',
            'To':   '%s@requests.muckrock.com, "Doe, John" <other@agency.gov>' % foia.get_mail_id(),
            'subject': 'Test subject',
            'stripped-text': 'Test normal.',
            'body-plain':    'Test normal.',
        }
        self.sign(data)
        response = self.client.post(
                reverse('mailgun-route'),
                data,
                **self.kwargs)
        nose.tools.eq_(response.status_code, 200)

        foia = FOIARequest.objects.get(pk=1)
        nose.tools.eq_(foia.get_emails(),
                (['test@agency.gov'], ['other@agency.gov']))

    def test_bad_sender(self):
        """Test a normal succesful response"""

        foia = FOIARequest.objects.get(pk=1)
        data = {
            'from': 'test@example.com',
            'From': 'test@example.com',
            'To':   '%s@requests.muckrock.com' % foia.get_mail_id(),
            'subject': 'Test subject',
            'stripped-text': 'Test bad sender.',
            'body-plain':    'Test bad sender.',
        }
        self.sign(data)
        response = self.client.post(
                reverse('mailgun-route'),
                data,
                **self.kwargs)
        nose.tools.eq_(response.status_code, 200)

    def test_bad_addr(self):
        """Test sending to a non existent FOIA request"""

        data = {
            'from': 'test@agency.gov',
            'From': 'test@agency.gov',
            'To':   '123-12345678@requests.muckrock.com',
            'subject': 'Test subject',
            'stripped-text': 'Test bad address.',
            'body-plain':    'Test bad address.',
        }
        self.sign(data)
        response = self.client.post(
                reverse('mailgun-route'),
                data,
                **self.kwargs)
        nose.tools.eq_(response.status_code, 200)

    def test_attachments(self):
        """Test a message with an attachment"""

        try:
            foia = FOIARequest.objects.get(pk=1)
            with open('data.xls', 'w') as file_:
                file_.write('abc123')
            data = {
                'from': 'test@agency.gov',
                'From': 'test@agency.gov',
                'To':   '%s@requests.muckrock.com' % foia.get_mail_id(),
                'subject': 'Test subject',
                'stripped-text': 'Test attachment.',
                'body-plain':    'Test attachment.',
                'attachment-1': open('data.xls'),
            }
            self.sign(data)
            response = self.client.post(
                    reverse('mailgun-route'),
                    data,
                    **self.kwargs)
            nose.tools.eq_(response.status_code, 200)

            foia = FOIARequest.objects.get(pk=1)
            file_path = date.today().strftime('foia_files/%Y/%m/%d/data.xls')
            nose.tools.eq_(foia.files.all()[0].ffile.name, file_path)

        finally:
            foia.files.all()[0].delete()
            os.remove('data.xls')
            file_path = os.path.join(settings.SITE_ROOT, 'static/media/', file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_fax(self):
        """Test a fax confirmation"""

        data = {
            'from': 'test@agency.gov',
            'From': 'test@agency.gov',
            'To':   'fax@requests.muckrock.com',
            'subject': 'Test subject',
            'stripped-text': 'Test fax.',
            'body-plain':    'Test fax.',
        }
        self.sign(data)
        response = self.client.post(reverse('mailgun-route'), data, **self.kwargs)
        nose.tools.eq_(response.status_code, 200)

        nose.tools.eq_(len(mail.outbox), 1)
        nose.tools.eq_(mail.outbox[0].body, 'Test fax.')
