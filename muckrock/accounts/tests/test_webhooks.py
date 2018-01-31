"""
Tests accounts webhook handling
"""

# Django
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

# Standard Library
import json

# Third Party
from mock import patch
from nose.tools import eq_

# MuckRock
from muckrock.accounts.views import stripe_webhook


class TestStripeWebhook(TestCase):
    """The Stripe webhook listens for events in order to issue receipts."""

    def setUp(self):
        self.mock_event = {
            'id': 'test-event',
            'type': 'mock.type',
            'data': {
                'object': {
                    'id': 'test-charge'
                }
            }
        }
        self.request_factory = RequestFactory()
        self.url = reverse('acct-webhook-v2')
        self.data = json.dumps(self.mock_event)

    def test_post_request(self):
        """Only POST requests should be allowed."""
        get_request = self.request_factory.get(self.url)
        response = stripe_webhook(get_request)
        eq_(response.status_code, 405, 'Should respond to GET request with 405')
        post_request = self.request_factory.post(
            self.url, data=self.data, content_type='application/json'
        )
        response = stripe_webhook(post_request)
        eq_(
            response.status_code, 200, 'Should respond to POST request with 200'
        )

    def test_bad_json(self):
        """POSTing bad JSON should return a 400 status code."""
        post_request = self.request_factory.post(
            self.url, data=u'Not JSON', content_type='application/json'
        )
        response = stripe_webhook(post_request)
        eq_(response.status_code, 400)

    def test_missing_data(self):
        """POSTing unexpected JSON should return a 400 status code."""
        bad_data = json.dumps({'hello': 'world'})
        post_request = self.request_factory.post(
            self.url, data=bad_data, content_type='application/json'
        )
        response = stripe_webhook(post_request)
        eq_(response.status_code, 400)

    @patch('muckrock.message.tasks.send_charge_receipt.delay')
    def test_charge_succeeded(self, mock_task):
        """When a charge succeeded event is received, send a charge receipt."""
        self.mock_event['type'] = 'charge.succeeded'
        post_request = self.request_factory.post(
            self.url,
            data=json.dumps(self.mock_event),
            content_type='application/json'
        )
        response = stripe_webhook(post_request)
        eq_(response.status_code, 200)
        mock_task.called_once()

    @patch('muckrock.message.tasks.send_invoice_receipt.delay')
    def test_invoice_succeeded(self, mock_task):
        """When an invoice payment succeeded event is received, send an invoice receipt."""
        self.mock_event['type'] = 'invoice.payment_succeeded'
        post_request = self.request_factory.post(
            self.url,
            data=json.dumps(self.mock_event),
            content_type='application/json'
        )
        response = stripe_webhook(post_request)
        eq_(response.status_code, 200)
        mock_task.called_once()

    @patch('muckrock.message.tasks.failed_payment.delay')
    def test_invoice_failed(self, mock_task):
        """When an invoice payment failed event is received, send a notification."""
        self.mock_event['type'] = 'invoice.payment_failed'
        post_request = self.request_factory.post(
            self.url,
            data=json.dumps(self.mock_event),
            content_type='application/json'
        )
        response = stripe_webhook(post_request)
        eq_(response.status_code, 200)
        mock_task.called_once()
