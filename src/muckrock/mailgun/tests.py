"""
Tests for mailgun
"""

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

import hashlib
import hmac
import nose.tools
import time

from foia.models import FOIARequest
from settings import MAILGUN_API_KEY

# allow methods that could be functions and too many public methods in tests
# pylint: disable=R0201
# pylint: disable=R0904

class TestMailgunViews(TestCase):
    """Tests for Mailgun views"""
    fixtures = ['test_users.json', 'test_profiles.json', 'jurisdictions.json',
                'test_foiarequests.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        mail.outbox = []

    def sign(self, data):
        """Add mailgun signature to data"""
        token = 'token'
        timestamp = int(time.time())
        signature = hmac.new(key=MAILGUN_API_KEY,
                             msg='%s%s' % (timestamp, token),
                             digestmod=hashlib.sha256).hexdigest()
        data['token'] = token
        data['timestamp'] = timestamp
        data['signature'] = signature

    def test_normal(self):
        """Test a normal succesful response"""

        foia = FOIARequest.objects.get(pk=1)
        data = {
            'from': 'test@agency.gov',
            'From': 'test@agency.gov',
            'To':   '%s@requests.muckrock.com, other@agency.gov' % foia.get_mail_id(),
            'subject': 'Test subject',
            'stripped-text': 'Test normal.',
            'body-plain':    'Test normal.',
        }
        self.sign(data)
        response = self.client.post(reverse('mailgun-request',
                                    kwargs={'mail_id': foia.get_mail_id()}), data)
        nose.tools.eq_(response.status_code, 200)

        nose.tools.eq_(len(mail.outbox), 3)
        nose.tools.eq_(mail.outbox[0].body, 'Test normal.')
        nose.tools.ok_(mail.outbox[1].subject.startswith('[RESPONSE]'))
        nose.tools.eq_(mail.outbox[2].to, [foia.user.email])

        foia = FOIARequest.objects.get(pk=1)
        nose.tools.eq_(foia.email, 'test@agency.gov')
        nose.tools.eq_(foia.other_emails, 'other@agency.gov')

