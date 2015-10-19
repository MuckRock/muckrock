from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import models


class DailyNotification(EmailMultiAlternatives):
    """Sends a daily email notification"""

    def __init__(self, user, **kwargs):
        """Initialize the notification"""
        super(DailyNotification, self).__init__(**kwargs)
        if isinstance(user, User):
            self.user = user
            self.to = [user.email]
        else:
            raise TypeError('Notification requires a User to recieve it')
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
