"""
Tasks for crowdfunds
"""

from celery.schedules import crontab
from celery.task import periodic_task
from datetime import date, timedelta

from muckrock.crowdfund.models import CrowdfundRequest, CrowdfundProject

@periodic_task(run_every=crontab(hour=0, minute=0), name='muckrock.crowdfund.tasks.close_expired')
def close_expired():
    """Close crowdfunds that were due yesterday"""
    yesterday = date.today() - timedelta(1)
    request_crowdfunds = CrowdfundRequest.objects.filter(date_due__lte=yesterday, closed=False)
    project_crowdfunds = CrowdfundProject.objects.filter(date_due__lte=yesterday, closed=False)
    for crowdfund in request_crowdfunds:
        crowdfund.close_crowdfund()
    for crowdfund in project_crowdfunds:
        crowdfund.close_crowdfund()
    return
