from django.db import models

from django.core.mail import EmailMessage, EmailMultiAlternatives

class DailyNotification(EmailMultiAlternatives):
    """Sends a daily email notification"""

    def __init__(self, **kwargs):
        """Initialize the notification"""
        super(DailyNotification, self).__init__(**kwargs)
