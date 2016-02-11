"""Celery Tasks for the agency application"""

from celery.schedules import crontab
from celery.task import periodic_task

from muckrock.agency.models import Agency
from muckrock.task.models import StaleAgencyTask

@periodic_task(run_every=crontab(day_of_week='sunday', hour=4, minute=0),
               name='muckrock.agency.tasks.stale')
def stale():
    """Record all stale agencies once a week"""
    for agency in Agency.objects.all():
        is_stale = agency.is_stale()
        if is_stale and not agency.stale:
            agency.stale = True
            agency.save()
            if not StaleAgencyTask.objects.filter(resolved=False, agency=agency).exists():
                StaleAgencyTask.objects.create(agency=agency)
        elif not is_stale and agency.stale:
            agency.stale = False
            agency.save()
            for task in StaleAgencyTask.objects.filter(resolved=False, agency=agency):
                task.resolve()
