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
from muckrock.foia.models import FOIARequest
from muckrock.task.models import ReviewAgencyTask

client = Client(os.environ.get('SENTRY_DSN'))
register_logger_signal(client)
register_signal(client)


@periodic_task(
    run_every=crontab(day_of_week='sunday', hour=4, minute=0),
    name='muckrock.agency.tasks.stale'
)
def stale():
    """Record all stale agencies once a week"""
    for foia in FOIARequest.objects.get_stale():
        ReviewAgencyTask.objects.ensure_one_created(
            agency=foia.agency,
            resolved=False,
        )
