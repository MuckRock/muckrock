"""
Digest objects for the messages app
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string

from actstream.models import Action, user_stream
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from muckrock.accounts.models import Statistics
from muckrock.foia.models import FOIARequest, FOIACommunication
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


class StaffDigest(Digest):
    """An email that digests other site stats for staff members."""
    text_template = 'message/staff_digest.txt'
    html_template = 'message/staff_digest.html'
    interval = relativedelta(days=1)

    def get_subject(self):
        """Does what it says on the box"""
        return 'Daily Staff Digest'

    def get_activity(self):
        """Returns yesterday's statistics"""

        # we overwrite the existing activity dictionary
        # and we fix count at 1 so the digest will send
        current_date = date.today() - self.interval
        previous_date = current_date - self.interval
        try:
            current = Statistics.objects.get(date=current_date)
            previous = Statistics.objects.get(date=previous_date)
        except Statistics.DoesNotExist:
            return {'count': 0} # if statistics cannot be found, don't send anything
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
                current.orphaned_communications,
                previous.orphaned_communications,
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
            'count': 1,
            'stats': stats,
            'comms': get_comms(current_date, previous_date),
        }

    def get_context_data(self):
        """Gathers what we need for the digest"""
        context = super(StaffDigest, self).get_context_data()
        current = datetime.now()
        context['yesterday'] = current - self.interval
        context['salutation'] = get_salutation(current.hour)
        context['signoff'] = get_signoff(current.hour)
        return context

    def send(self, *args):
        """Don't send to users who are not staff"""
        if not self.user.is_staff:
            return 0
        return super(StaffDigest, self).send(*args)

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
        }
    }

def get_salutation(hour):
    """Returns a time-appropriate salutation"""
    if hour < 12:
        salutation = 'Good morning'
    elif hour < 18:
        salutation = 'Good afternoon'
    else:
        salutation = 'Good evening'
    return salutation

def get_signoff(hour):
    """Returns a time-appropriate signoff"""
    if hour < 18:
        signoff = 'Have a great day'
    else:
        signoff = 'Have a great night'
    return signoff
