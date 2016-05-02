"""
Notification objects for the messages app
"""

from django.conf import settings

import json
import requests

class SlackNotification(object):
    """
    Sends a Slack notification, conforming to the platform's specification.
    Slack notifications should be initialized with a payload that contains the notification.
    If they aren't, you still have a chance to update the payload before sending the message.
    Notifications with empty payloads will be rejected by Slack.
    Payload should be a dictionary, and the API is described by Slack here:
    https://api.slack.com/docs/formatting
    https://api.slack.com/docs/attachments
    """
    def __init__(self, payload=None):
        """Initializes the request with a payload"""
        self.endpoint = settings.SLACK_WEBHOOK_URL
        if payload is None:
            payload = {}
        self.payload = payload

    def send(self, fail_silently=True):
        """Send the notification to our Slack webhook."""
        if not self.endpoint:
            # don't send when the endpoint value is empty,
            # or the requests module will throw errors like woah
            return 0
        data = json.dumps(self.payload)
        response = requests.post(self.endpoint, data=data)
        if response.status_code == 200:
            return 1
        else:
            if not fail_silently:
                response.raise_for_status()
            return 0
