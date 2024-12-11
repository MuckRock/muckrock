"""
Tasks for crowdfunds
"""

# Django
from celery import shared_task
from celery.schedules import crontab

# Standard Library
from datetime import date, timedelta

# MuckRock
from muckrock.crowdfund.models import Crowdfund


@shared_task
def close_expired():
    """Close crowdfunds that were due yesterday"""
    yesterday = date.today() - timedelta(1)
    crowdfunds = Crowdfund.objects.filter(date_due__lte=yesterday, closed=False)
    for crowdfund in crowdfunds:
        crowdfund.close_crowdfund()
