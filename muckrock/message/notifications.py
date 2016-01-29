"""
Notification objects for the messages app
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import json
import requests

from muckrock.settings import SLACK_WEBHOOK_URL

class EmailNotification(EmailMultiAlternatives):
    """A generic base class for composing notification emails."""
    text_template = None
    subject = u'Notification'

    def __init__(self, user, context):
        """Initialize the notification"""
        super(EmailNotification, self).__init__(subject=self.subject)
        if isinstance(user, User):
            self.user = user
            self.to = [user.email]
        else:
            raise TypeError('Notification requires a User to receive it.')
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
        self.body = render_to_string(self.get_text_template(), self.get_context_data(context))

    def get_context_data(self, context):
        """Return init keywords and the user-to-notify as context."""
        context['user'] = self.user
        return context

    def get_text_template(self):
        """Every notification should have a text template."""
        if self.text_template == None:
            raise NotImplementedError('Notification requires a text template.')
        else:
            return self.text_template


class FailedPaymentNotification(EmailNotification):
    """Sends a failed payment notification"""
    text_template = 'message/notification/failed_payment.txt'
    subject = u'Your payment failed'


class WelcomeNotification(EmailNotification):
    """Sends a welcome notification"""
    text_template = 'text/user/welcome.txt'
    subject = u'Welcome to MuckRock'


class GiftNotification(EmailNotification):
    """Sends a gift notification to the receipient"""
    text_template = 'message/notification/gift.txt'
    subject = u'You have a gift'


class EmailChangeNotification(EmailNotification):
    """Sends an email confirming an email change"""
    text_template = 'message/notification/email_change.txt'
    subject = u'Changed email address'


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
    endpoint = SLACK_WEBHOOK_URL

    def __init__(self, payload=None):
        """Initializes the request with a payload"""
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
