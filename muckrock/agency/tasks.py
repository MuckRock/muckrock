"""Celery Tasks for the agency application"""

from celery.schedules import crontab
from celery.task import periodic_task

from muckrock.agency.models import Agency, STALE_DURATION
from muckrock.task.models import StaleAgencyTask

@periodic_task(run_every=crontab(day_of_week='sunday', hour=4, minute=0),
               name='muckrock.agency.tasks.stale')
def stale():
    """Record all stale agencies once a week"""
    for agency in Agency.objects.all():
        latest_response = agency.latest_response()
        is_stale = latest_response is not None and latest_response >= STALE_DURATION
        if is_stale or agency.expired():
            agency.stale = True
            agency.save()
            if not StaleAgencyTask.objects.filter(resolved=False, agency=agency).exists():
                StaleAgencyTask.objects.create(agency=agency)
