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

    # Here we scaffold out the activity dictionary.
    # It is scaffolded to prevent key errors when counting
    # activity, as well as to provide some guidance for
    # which activities to filter from the global stream.

    # Activity is independent from template context because
    # we use activity counts to influence other parts of the
    # email, like the subject line and whether or not to
    # even send the email at all.

    activity = {
        'count': 0,
        'requests': {
            'count': 0,
            'mine': None,
            'following': None
        },
        'questions': {
            'count': 0,
            'mine': None,
            'following': None
        }
    }

    # Most of the work re: composing the email takes place
    # at init. This is by design, since digests should require
    # a minimum of configuration outside of their own configuration,
    # which is their responsibility. In other words, a digest really
    # only needs to know its user.

    # Question: should interval be made into a required init value?
    # On the one hand, having interval hardcoded into subclasses is
    # less flexible. On the other, this flexibility might not be required
    # beyond specifically-defined subclasses.

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
        text_email = render_to_string(self.text_template, context)
        html_email = render_to_string(self.html_template, context)
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
        self.subject = self.get_subject()
        self.body = text_email
        self.attach_alternative(html_email, 'text/html')

    def model_stream(self, model, stream):
        """Helper function to extract actions from stream by model"""
        # pylint: disable=no-self-use
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
        foia_stream = self.classify_foia_activity(foia_stream)
        foia_following = self.classify_foia_activity(foia_following)
        self.activity['requests'] = {
            'count': foia_stream['count'] + foia_following['count'],
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
        context = {
            'user': self.user,
            'activity': self.activity,
            'base_url': 'https://www.muckrock.com'
        }
        return context

    def classify_foia_activity(self, stream):
        """Segment and classify the activity"""
        # pylint: disable=no-self-use
        classified = {
            'completed': stream.filter(verb__icontains='completed'),
            'rejected': stream.filter(verb__icontains='rejected'),
            'unsuccessful': stream.filter(verb__icontains='no responsive documents'),
            'action_required': stream.filter(
                Q(verb__icontains='payment')|Q(verb__icontains='fix')),
            'response': stream.filter(
                Q(verb__icontains='processing')|Q(verb__icontains='acknowledged')),
        }
        activity_count = 0
        for _, classified_stream in classified.iteritems():
            activity_count += len(classified_stream)
        classified['count'] = activity_count
        return classified

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
