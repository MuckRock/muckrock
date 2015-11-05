"""
Notification objects for the messages app
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import actstream
import datetime
import logging

def get_foia_activity(user, period):
    """Returns a sorted collection of FOIA activity."""
    foia_stream = actstream.models.Action.objects.requests_for_user(user)
    foia_stream = foia_stream.filter(timestamp__gte=period)
    # we sort the items in the foia stream to figure out their priority
    finished_verbs = ['completed', 'rejected', 'partially completed']
    attention_verbs = ['requires fix', 'requires payment']
    foia_actions = {
        'count': foia_stream.count(),
        'finished': [],
        'attention': [],
        'other': []
    }
    for foia_action in foia_stream:
        if foia_action.verb in finished_verbs:
            foia_actions['finished'].append(foia_action)
        elif foia_action.verb in attention_verbs:
            foia_actions['attention'].append(foia_action)
        else:
            foia_actions['other'].append(foia_action)
    return foia_actions


class DailyNotification(EmailMultiAlternatives):
    """Sends a daily email notification"""

    text_template = 'notification/daily.txt'
    html_template = 'notification/daily.html'

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

    def send(self, *args):
        """Don't send the email if there's no notifications."""
        if self.notification_count == 0:
            return 0
        return super(DailyNotification, self).send(*args)

    def compose(self):
        """Compose the email"""
        activity = self.get_activity()
        self.notification_count = activity['following'].count() + activity['requests']['count']
        show_requests = activity['requests']['count'] > 0
        show_following = activity['following'].count() > 0
        show_headings = show_requests and show_following
        context = {
            'user': self.user,
            'show_headings': show_headings,
            'show_requests': show_requests,
            'show_following': show_following,
            'attention_foia': activity['requests']['attention'],
            'finished_foia': activity['requests']['finished'],
            'other_foia': activity['requests']['other'],
            'following': activity['following'],
            'count': self.notification_count,
            'since': self.since,
            'base_url': 'https://www.muckrock.com'
        }
        logging.info(context)
        text_content = render_to_string(self.text_template, context)
        html_content = render_to_string(self.html_template, context)
        self.subject = self.get_subject()
        self.body = text_content
        self.attach_alternative(html_content, 'text/html')
        return

    def get_activity(self):
        """Returns a list of activities to be sent in the email"""
        period = datetime.datetime.now() - datetime.timedelta(1)
        foia_activity = get_foia_activity(self.user, period)
        user_stream = actstream.models.user_stream(self.user)
        user_stream = user_stream.filter(timestamp__gte=period).exclude(verb__icontains='following')
        return {
            'requests': foia_activity,
            'following': user_stream
        }

    def get_subject(self):
        """Summarizes the activities in the notificiation"""
        noun = 'update' if self.notification_count == 1 else 'updates'
        subject = '%d %s %s' % (self.notification_count, noun, self.since)
        return subject


class FailedPaymentNotification(EmailMultiAlternatives):
    """Sends a failed payment notification"""
    def __init__(self, user, attempt, **kwargs):
        """Initialize the notification"""
        super(FailedPaymentNotification, self).__init__(**kwargs)
        if isinstance(user, User):
            self.user = user
            self.to = [user.email]
        else:
            raise TypeError('Notification requires a User to recieve it.')
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
        self.subject = 'Payment Failed'
        self.body = render_to_string(
            'notification/failed_payment.txt',
            {'user': self.user, 'attempt': attempt}
        )
