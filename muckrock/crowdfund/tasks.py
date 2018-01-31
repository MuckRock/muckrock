"""
Tasks for crowdfunds
"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task

# Standard Library
from datetime import date, timedelta

# MuckRock
from muckrock.crowdfund.models import Crowdfund


@periodic_task(
    run_every=crontab(hour=0, minute=0),
    name='muckrock.crowdfund.tasks.close_expired'
)
def close_expired():
    """Close crowdfunds that were due yesterday"""
    yesterday = date.today() - timedelta(1)
    crowdfunds = Crowdfund.objects.filter(date_due__lte=yesterday, closed=False)
    for crowdfund in crowdfunds:
        crowdfund.close_crowdfund()
