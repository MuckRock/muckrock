"""
Digest objects for the messages app
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from actstream.models import Action, user_stream
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from muckrock.accounts.models import Statistics
from muckrock.message.email import TemplateEmail
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.qanda.models import Question

def model_stream(model, stream):
    """Filter stream by model"""
    content_type = ContentType.objects.get_for_model(model)
    action_object = Q(action_object_content_type=content_type)
    target = Q(target_content_type=content_type)
    return stream.filter(action_object|target)

def stat(name, current, previous, growth=True):
    """Returns a statistic dictionary"""
    return {
        'name': name,
        'current': current,
        'delta': current - previous,
        'growth': growth
    }

def get_comms(current, previous):
    """Returns a dictionary of communications"""
    received = FOIACommunication.objects.filter(date__range=[previous, current], response=True)
    sent = FOIACommunication.objects.filter(date__range=[previous, current], response=False)
    delivered_by = {
        'email': sent.filter(delivered='email').count(),
        'fax': sent.filter(delivered='fax').count(),
        'mail': sent.filter(delivered='mail').count()
    }
    cost_per = {
        'email': 0.00,
        'fax': 0.12,
        'mail': 0.54,
    }
    cost = {
        'email': delivered_by['email'] * cost_per['email'],
        'fax': delivered_by['fax'] * cost_per['fax'],
        'mail': delivered_by['mail'] * cost_per['mail'],
    }
    return {
        'sent': sent.count(),
        'received': received.count(),
        'delivery': {
            'format': delivered_by,
            'cost': cost_per,
            'expense': cost,
            'trailing': get_trailing_cost(current, 30, cost_per)
        }
    }

def get_trailing_cost(current, duration, cost_per):
    """Returns the trailing cost for communications over a period"""
    period = [current - relativedelta(days=duration), current]
    sent_comms = FOIACommunication.objects.filter(date__range=period, response=False)
    trailing = {
        'email': sent_comms.filter(delivered='email').count(),
        'fax': sent_comms.filter(delivered='fax').count(),
        'mail': sent_comms.filter(delivered='mail').count()
    }
    trailing_cost = {
        'email': trailing['email'] * cost_per['email'],
        'fax': trailing['fax'] * cost_per['fax'],
        'mail': trailing['mail'] * cost_per['mail']
    }
    return trailing_cost

def get_salutation():
    """Returns a time-appropriate salutation"""
    hour = timezone.now().hour
    if hour < 12:
        salutation = 'Good morning'
    elif hour < 18:
        salutation = 'Good afternoon'
    else:
        salutation = 'Good evening'
    return salutation

def get_signoff():
    """Returns a time-appropriate signoff"""
    hour = timezone.now().hour
    if hour < 18:
        signoff = 'Have a great day'
    else:
        signoff = 'Have a great night'
    return signoff


class Digest(TemplateEmail):
    """A digest is sent at a regular scheduled interval."""
    interval = None

    def __init__(self, interval=None, **kwargs):
        """Saves interval attribute if provided."""
        if interval:
            # we use relativedelta in addition to timedelta because it gives us a greater
            # flexibility in the kinds of intervals we can define, e.g. weeks and months
            if isinstance(interval, relativedelta) or isinstance(interval, timedelta):
                self.interval = interval
            else:
                raise TypeError('Interval must be relativedelta or timedelta')
        super(Digest, self).__init__(**kwargs)

    def get_context_data(self, *args):
        """Adds time-based salutation and signature context"""
        context = super(Digest, self).get_context_data(*args)
        context['salutation'] = get_salutation()
        context['signoff'] = get_signoff()
        context['last'] = self.get_duration()
        return context

    def get_duration(self):
        """Returns the start of the duration for the digest."""
        return timezone.now() - self.get_interval()

    def get_interval(self):
        """Gets the interval or raises an error if it is missing or an unexpected type."""
        if not self.interval:
            raise NotImplementedError('Interval must be provided by subclass or when initialized.')
        return self.interval


class ActivityDigest(Digest):
    """
    An ActivityDigest describes a collection of activity over a duration, which
    is then rendered into an email and delivered at a scheduled interval.
    """
    text_template = 'message/digest/digest.txt'
    html_template = 'message/digest/digest.html'

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

    def __init__(self, **kwargs):
        """Initialize the digest with a dynamic subject."""
        super(ActivityDigest, self).__init__(**kwargs)
        self.subject = self.get_subject()

    def get_context_data(self, *args):
        """Adds classified activity to the context."""
        context = super(ActivityDigest, self).get_context_data(*args)
        context['activity'] = self.get_activity()
        context['subject'] = self.get_subject()
        context['summary'] = self.summarize_activity()
        return context

    def get_activity(self):
        """Returns a list of activities to be sent in the email"""
        duration = self.get_duration()
        user_ct = ContentType.objects.get_for_model(self.user)
        following = (user_stream(self.user).filter(timestamp__gte=duration)
                                           .exclude(verb__icontains='following'))
        foia_following = model_stream(FOIARequest, following)
        question_following = model_stream(Question, following).exclude(verb='asked')
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
        """Summarizes the activities in the notification."""
        count = self.activity['count']
        subject = str(count) + ' Update'
        if count > 1:
            subject += 's'
        return self.subject + ': ' + subject

    def summarize_activity(self):
        """Summarizes the activity in the digest."""
        return u''

    def send(self, *args):
        """Don't send the email if there's no activity."""
        if self.activity['count'] < 1:
            return 0
        return super(Digest, self).send(*args)


class StaffDigest(Digest):
    """An email that digests other site stats for staff members."""
    text_template = 'message/digest/staff_digest.txt'
    html_template = 'message/digest/staff_digest.html'
    interval = relativedelta(days=1)

    def get_context_data(self, *args):
        """Adds classified activity to the context"""
        context = super(StaffDigest, self).get_context_data(*args)
        self.activity = self.get_activity()
        context['activity'] = self.activity
        return context

    def get_activity(self):
        """Returns yesterday's statistics"""
        current_date = timezone.now() - self.interval
        previous_date = current_date - self.interval
        try:
            current = Statistics.objects.get(date=current_date)
            previous = Statistics.objects.get(date=previous_date)
        except Statistics.DoesNotExist:
            return None # if statistics cannot be found, don't send anything
        stats = [
            stat('Requests', current.total_requests, previous.total_requests),
            stat(
                'Processing',
                current.total_requests_submitted,
                previous.total_requests_submitted,
                False
            ),
            stat(
                'Processing Time',
                current.requests_processing_days,
                previous.requests_processing_days,
                False
            ),
            stat(
                'Unresolved Tasks',
                current.total_unresolved_tasks,
                previous.total_unresolved_tasks,
                False
            ),
            stat(
                'Automatically Resolved',
                current.daily_robot_response_tasks,
                previous.daily_robot_response_tasks
            ),
            stat(
                'Orphans',
                current.total_unresolved_orphan_tasks,
                previous.total_unresolved_orphan_tasks,
                False
            ),
            stat('Pages', current.total_pages, previous.total_pages),
            stat('Users', current.total_users, previous.total_users),
            stat('Pro Users', current.pro_users, previous.pro_users),
            stat('Agencies', current.total_agencies, previous.total_agencies),
            stat('Stale Agencies', current.stale_agencies, previous.stale_agencies, False),
            stat('New Agencies', current.unapproved_agencies, previous.unapproved_agencies, False),
        ]
        return {
            'stats': stats,
            'comms': get_comms(current_date, previous_date),
        }

    def send(self, *args):
        """Don't send to users who are not staff"""
        if not self.user.is_staff:
            return 0
        return super(StaffDigest, self).send(*args)
