from django.db import models

from django.core.mail import EmailMessage, EmailMultiAlternatives

class DailyNotification(EmailMultiAlternatives):
    """Sends a daily email notification"""
    pass
