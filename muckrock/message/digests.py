"""
Digest objects for the messages app
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from actstream.models import Action, user_stream
from datetime import datetime, timedelta
import logging

class Digest(EmailMultiAlternatives):
    """
    A digest is a collection of activity over a duration,
    generated and delivered at a scheduled interval.
    """
    text_template = None
    html_template = None
    interval = None

    def __init__(self, user, **kwargs):
        """Initialize the notification"""
        super(Digest, self).__init__(**kwargs)
        if isinstance(user, User):
            self.user = user
            self.to = [user.email]
        else:
            raise TypeError('Digest requires a User to recieve it')
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
        self.activity = self.get_activity()
        self.notification_count = self.activity['count']
        context = self.get_context_data()
        text_email = render_to_string(self.get_text_template(), context)
        html_email = render_to_string(self.get_html_template(), context)
        self.subject = self.get_subject()
        self.body = text_email
        self.attach_alternative(html_email, 'text/html')

    def send(self, *args):
        """Don't send the email if there's no notifications."""
        if self.notification_count < 1:
            return 0
        return super(Digest, self).send(*args)

    def get_context_data(self):
        """Returns context for the digest"""
        context = {'user': self.user}
        return context

    def get_text_template(self):
        """Returns the text template"""
        if not self.text_template:
            raise NotImplementedError('No text template specified.')
        return self.text_template

    def get_html_template(self):
        """Returns the html template"""
        if not self.html_template:
            raise NotImplementedError('No HTML template specified.')
        return self.html_template

    def get_subject(self):
        """Summarizes the activities in the notification"""
        subject = str(self.notification_count) + ' Update'
        if self.notification_count > 1:
            subject += 's'
        return subject

    def get_duration(self):
        if not self.interval:
            raise NotImplementedError('No interval specified.')
        if not isinstance(self.interval, timedelta):
            raise TypeError('Interval attribute must be a datetime.timedelta object.')
        return datetime.now() - self.interval

    def get_foia_activity(self, period):
        """Returns a sorted collection of FOIA activity."""
        foia_stream = Action.objects.requests_for_user(self.user)
        foia_stream = foia_stream.filter(timestamp__gte=period)
        user_ct = ContentType.objects.get_for_model(self.user)
        # exclude actions where the user is the Actor
        # since they know which actions they've taken themselves
        foia_stream.exclude(actor_content_type=user_ct, actor_object_id=self.user.id)
        return foia_stream

    def get_activity(self):
        """Returns a list of activities to be sent in the email"""
        duration = self.get_duration()
        f_stream = self.get_foia_activity(duration)
        u_stream = user_stream(self.user).filter(timestamp__gte=duration)\
                                         .exclude(verb__icontains='following')
        return {
            'count': f_stream.count() + u_stream.count(),
            'requests': f_stream,
            'following': u_stream
        }


class DailyDigest(Digest):
    """Sends a daily email digest"""

    text_template = 'message/notification/daily.txt'
    html_template = 'message/notification/daily.html'
    interval = timedelta(days=1)

    def get_context_data(self):
        """Compose the email"""
        context = super(DailyDigest, self).get_context_data()
        show_requests = self.activity['requests'].count() > 0
        show_following = self.activity['following'].count() > 0
        show_headings = show_requests and show_following
        context.update({
            'show_headings': show_headings,
            'show_requests': show_requests,
            'show_following': show_following,
            'requests': self.activity['requests'],
            'following': self.activity['following'],
            'count': self.activity['count'],
            'base_url': 'https://www.muckrock.com'
        })
        return context




