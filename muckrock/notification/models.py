from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string

import actstream
import datetime

class DailyNotification(EmailMultiAlternatives):
    """Sends a daily email notification"""

    notification_count = 0
    since = 'yesterday'

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
        self.compose()

    def compose(self):
        """Compose the email"""
        activity = self.get_activity()
        self.notification_count = len(activity)
        text_content = render_to_string('email/activity.txt', {
            'user': self.user,
            'stream': activity,
            'count': self.notification_count,
            'since': self.since
        })
        html_content = render_to_string('email/activity.html', {
            'user': self.user,
            'stream': activity,
            'count': self.notification_count,
            'since': self.since,
            'base_url': 'https://www.muckrock.com'
        })
        self.subject = self.get_subject()
        self.body = text_content
        self.attach_alternative(html_content, 'text/html')
        return

    def get_activity(self):
        """Returns a list of activities to be sent in the email"""
        current_time = datetime.datetime.now()
        period_start = current_time - datetime.timedelta(1)
        user_stream = actstream.models.user_stream(self.user)
        user_stream = user_stream.filter(timestamp__gte=period_start)\
                                 .exclude(verb='started following')
        return list(user_stream)

    def get_subject(self):
        """Summarizes the activities in the notificiation"""
        noun = 'update' if self.notification_count == 1 else 'updates'
        subject = '%d %s %s' % (self.notification_count, noun, self.since)
        return subject
