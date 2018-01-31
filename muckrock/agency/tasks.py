"""Celery Tasks for the agency application"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task

# Standard Library
import os

# Third Party
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal

# MuckRock
from muckrock.agency.models import Agency
from muckrock.task.models import StaleAgencyTask

client = Client(os.environ.get('SENTRY_DSN'))
register_logger_signal(client)
register_signal(client)


@periodic_task(
    run_every=crontab(day_of_week='sunday', hour=4, minute=0),
    name='muckrock.agency.tasks.stale'
)
def stale():
    """Record all stale agencies once a week"""
    for agency in Agency.objects.all():
        is_stale = agency.is_stale()
        if is_stale and not agency.stale:
            agency.mark_stale()
        elif not is_stale and agency.stale:
            agency.unmark_stale()
            for task in StaleAgencyTask.objects.filter(
                resolved=False, agency=agency
            ):
                task.resolve()
