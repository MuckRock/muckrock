"""
Digest objects for the messages app
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string

from actstream.models import Action, user_stream
from datetime import datetime
from dateutil.relativedelta import relativedelta

from muckrock.foia.models import FOIARequest
from muckrock.qanda.models import Question

class Digest(EmailMultiAlternatives):
    """
    A digest describes a collection of activity over a duration, which
    is then rendered into an email and delivered at a scheduled interval.
    """
    text_template = 'message/digest.txt'
    html_template = 'message/digest.html'
    interval = None
    activity = {
        'count': 0,
        'requests': None,
        'following': None
    }

    def __init__(self, user, **kwargs):
        """Initialize the notification"""
        super(Digest, self).__init__(**kwargs)
        if isinstance(user, User):
            self.user = user
            self.to = [user.email]
        else:
            raise TypeError('Digest requires a User to recieve it')
        self.activity = self.get_activity()
        context = self.get_context_data()
        text_email = render_to_string(self.get_text_template(), context)
        html_email = render_to_string(self.get_html_template(), context)
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
        self.subject = self.get_subject()
        self.body = text_email
        self.attach_alternative(html_email, 'text/html')

    def model_stream(self, model, stream):
        """Extract actions from stream by model"""
        content_type = ContentType.objects.get_for_model(model)
        action_object = Q(action_object_content_type=content_type)
        target = Q(target_content_type=content_type)
        return stream.filter(action_object|target)

    def get_activity(self):
        """Returns a list of activities to be sent in the email"""
        duration = self.get_duration()
        user_ct = ContentType.objects.get_for_model(self.user)
        following = (user_stream(self.user).filter(timestamp__gte=duration)
                                           .exclude(verb__icontains='following'))
        foia_following = self.model_stream(FOIARequest, following)
        question_following = self.model_stream(Question, following).exclude(verb='asked')
        foia_stream = (Action.objects.owned_by(self.user, FOIARequest)
                                     .filter(timestamp__gte=duration)
                                     .exclude(actor_content_type=user_ct,
                                              actor_object_id=self.user.id))
        question_stream = (Action.objects.owned_by(self.user, Question)
                                         .filter(timestamp__gte=duration)
                                         .exclude(actor_content_type=user_ct,
                                                  actor_object_id=self.user.id))
        self.activity['requests'] = {
            'count': foia_stream.count() + foia_following.count(),
            'mine': foia_stream,
            'following': foia_following
        }
        self.activity['questions'] = {
            'count': question_stream.count() + question_following.count(),
            'mine': question_stream,
            'following': question_following
        }
        self.activity['count'] = (self.activity['requests']['count'] +
                                  self.activity['questions']['count'])
        return self.activity

    def get_duration(self):
        """Returns the start of the duration of activity for the digest."""
        if not self.interval:
            raise NotImplementedError('No interval specified.')
        if not isinstance(self.interval, relativedelta):
            # we use relativedelta instead of timedelta because it gives us a greater
            # flexibility in the kinds of intervals we can define, e.g. weeks and months
            raise TypeError('Interval must be a dateutil.relativedelta.relativedelta object.')
        return datetime.now() - self.interval

    def get_context_data(self):
        """Adds classified activity to the context"""
        classified_foia_activity = self.classify_foia_activity()
        context = {
            'user': self.user,
            'activity': self.activity,
            'foia_activity': classified_foia_activity,
            'base_url': 'https://www.muckrock.com'
        }
        return context

    def classify_foia_activity(self):
        """Segment and classify the activity"""
        foia_activity = self.activity['requests']['mine']
        return {
            'granted': foia_activity.filter(verb__icontains='completed'),
            'denied': foia_activity.filter(verb__icontains='rejected'),
            'unsuccessful': foia_activity.filter(verb__icontains='no responsive documents'),
            'payment': foia_activity.filter(verb__icontains='payment'),
            'fix': foia_activity.filter(verb__icontains='fix'),
            'unembargo': foia_activity.filter(verb__icontains='unembargo'),
            'response': foia_activity.filter(verb__icontains='responded'),
            'auto_follow_up': foia_activity.filter(verb__icontains='automatically followed up'),
        }

    def get_text_template(self):
        """Returns the text template"""
        return self.text_template

    def get_html_template(self):
        """Returns the html template"""
        return self.html_template

    def get_subject(self):
        """Summarizes the activities in the notification"""
        subject = str(self.activity['count']) + ' Update'
        if self.activity['count'] > 1:
            subject += 's'
        return subject

    def send(self, *args):
        """Don't send the email if there's no activity."""
        if self.activity['count'] < 1:
            return 0
        return super(Digest, self).send(*args)


class HourlyDigest(Digest):
    """An hourly email digest"""
    interval = relativedelta(hours=1)


class DailyDigest(Digest):
    """A daily email digest"""
    interval = relativedelta(days=1)


class WeeklyDigest(Digest):
    """A weekly email digest"""
    interval = relativedelta(weeks=1)


class MonthlyDigest(Digest):
    """A monthly email digest"""
    interval = relativedelta(months=1)
