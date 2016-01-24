"""
Notification objects for the messages app
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

class Notification(EmailMultiAlternatives):
    """A generic base class for composing notification emails."""
    text_template = None
    subject = u'Notification'

    def __init__(self, user, context):
        """Initialize the notification"""
        super(Notification, self).__init__(subject=self.subject)
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


class FailedPaymentNotification(Notification):
    """Sends a failed payment notification"""
    text_template = 'message/notification/failed_payment.txt'
    subject = u'Your payment failed'


class WelcomeNotification(Notification):
    """Sends a welcome notification"""
    text_template = 'text/user/welcome.txt'
    subject = u'Welcome to MuckRock'


class GiftNotification(Notification):
    """Sends a gift notification to the receipient"""
    text_template = 'message/notification/gift.txt'
    subject = u'You have a gift'


class EmailChangeNotification(Notification):
    """Sends an email confirming an email change"""
    text_template = 'message/notification/email_change.txt'
    subject = u'Changed email address'

