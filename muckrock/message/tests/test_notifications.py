"""
Tests the notification objects.
"""

# Django
from django.test import TestCase
from django.test.utils import override_settings

# Standard Library
import json

# Third Party
from mock import patch

# MuckRock
from muckrock.message.notifications import SlackNotification


@override_settings(SLACK_WEBHOOK_URL='http://www.example.com')
class TestSlackNotifications(TestCase):
    """Check that Slack notifications send to the correct endpoint."""

    def setUp(self):
        payload = {'text': 'Test'}
        self.slack = SlackNotification(payload)

    @patch('requests.post')
    def test_send(self, mock_post):
        """Sending should post the payload to the endpoint."""
        endpoint = self.slack.endpoint
        data = json.dumps(self.slack.payload)
        self.slack.send()
        mock_post.assert_called_with(endpoint, data=data)
