"""
Tasks for the messages application.
"""

# Django
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.contrib.auth.models import User
from django.utils import timezone

# Standard Library
import logging
from random import randint

# Third Party
from dateutil.relativedelta import relativedelta
from requests.exceptions import RequestException

# MuckRock
from muckrock.message import digests
from muckrock.message.email import TemplateEmail
from muckrock.message.notifications import SlackNotification

logger = logging.getLogger(__name__)


@task(
    time_limit=600,
    soft_time_limit=570,
    name='muckrock.message.tasks.send_activity_digest',
)
def send_activity_digest(user, subject, interval):
    """Individual task to create and send an activity digest to a user."""
    logger.info(
        'Starting activity digest at: %s User: %s Subject: %s Interval: %s',
        timezone.now(), user, subject, interval
    )
    try:
        email = digests.ActivityDigest(
            user=user,
            subject=subject,
            interval=interval,
        )
        email.send()
    except SoftTimeLimitExceeded:
        logger.error(
            'Send Activity Digest took too long. '
            'User: %s, Subject: %s, Interval %s', user, subject, interval
        )


def send_digests(preference, subject, interval):
    """Helper to send out timed digests"""
    users = (
        User.objects.filter(
            profile__email_pref=preference,
            notifications__read=False,
        ).distinct()
    )
    for user in users:
        send_activity_digest.delay(user, subject, interval)


# every hour
@periodic_task(
    run_every=crontab(hour='*/1', minute=0),
    name='muckrock.message.tasks.hourly_digest'
)
def hourly_digest():
    """Send out hourly digest"""
    send_digests('hourly', u'Hourly Digest', relativedelta(hours=1))


# every day at 10am
@periodic_task(
    run_every=crontab(hour=10, minute=0),
    name='muckrock.message.tasks.daily_digest'
)
def daily_digest():
    """Send out daily digest"""
    send_digests('daily', u'Daily Digest', relativedelta(days=1))


# every Monday at 10am
@periodic_task(
    run_every=crontab(day_of_week=1, hour=10, minute=0),
    name='muckrock.message.tasks.weekly_digest'
)
def weekly_digest():
    """Send out weekly digest"""
    send_digests('weekly', u'Weekly Digest', relativedelta(weeks=1))


# first day of every month at 10am
@periodic_task(
    run_every=crontab(day_of_month=1, hour=10, minute=0),
    name='muckrock.message.tasks.monthly_digest'
)
def monthly_digest():
    """Send out monthly digest"""
    send_digests('monthly', u'Monthly Digest', relativedelta(months=1))


# every day at 9:30am
@periodic_task(
    run_every=crontab(hour=9, minute=30),
    name='muckrock.message.tasks.staff_digest'
)
def staff_digest():
    """Send out staff digest"""
    staff_users = User.objects.filter(is_staff=True).distinct()
    for staff_user in staff_users:
        email = digests.StaffDigest(
            user=staff_user, subject=u'Daily Staff Digest'
        )
        email.send()


@task(name='muckrock.message.tasks.support')
def support(user, message, _task):
    """Send a response to a user about a task."""
    context = {'message': message, 'task': _task}
    notification = TemplateEmail(
        user=user,
        extra_context=context,
        text_template='message/notification/support.txt',
        html_template='message/notification/support.html',
        subject=u'Support #%d' % _task.id
    )
    notification.send(fail_silently=False)


@task(name='muckrock.message.tasks.notify_project_contributor')
def notify_project_contributor(user, project, added_by):
    """Notify a user that they were added as a contributor to a project."""
    context = {'project': project, 'added_by': added_by}
    notification = TemplateEmail(
        user=user,
        extra_context=context,
        text_template='message/notification/project.txt',
        html_template='message/notification/project.html',
        subject=u'Added to a project'
    )
    notification.send(fail_silently=False)


@task(name='muckrock.message.tasks.slack')
def slack(payload):
    """Send a Slack notification using the provided payload."""
    try:
        notification = SlackNotification(payload)
        notification.send(fail_silently=False)
    except RequestException as exc:
        slack.retry(
            countdown=2 ** slack.request.retries * 30 + randint(0, 30),
            args=[payload],
            exc=exc,
        )


@task(name='muckrock.message.tasks.gift')
def gift(to_user, from_user, gift_description):
    """Notify the user when they have been gifted requests."""
    context = {'from': from_user, 'gift': gift_description}
    notification = TemplateEmail(
        user=to_user,
        extra_context=context,
        text_template='message/notification/gift.txt',
        html_template='message/notification/gift.html',
        subject=u'You got a gift!'
    )
    notification.send(fail_silently=False)
