
"""
Tasks for the account application
"""

from celery.decorators import periodic_task
from celery.schedules import crontab
from django.contrib.auth.models import User
from django.db.models import Sum
from sentry.client.handlers import SentryHandler

import logging
from datetime import date, timedelta

from accounts.models import Statistics
from foia.models import FOIARequest, FOIADocument, Agency

logger = logging.getLogger('task')
logger.setLevel(logging.INFO)
if SentryHandler not in [x.__class__ for x in logger.handlers]:
    logger.addHandler(SentryHandler())

@periodic_task(run_every=crontab(hour=0, minute=30))
def store_statstics():
    """Store the daily statistics"""

    yesterday = date.today() - timedelta(1)

    stats = Statistics.objects.create(
        date=yesterday,
        total_requests=FOIARequest.objects.count(),
        total_requests_success=FOIARequest.objects.filter(status='done').count(),
        total_requests_denied=FOIARequest.objects.filter(status='rejected').count(),
        total_pages=FOIADocument.objects.aggregate(Sum('pages'))['pages__sum'],
        total_users=User.objects.count(),
        total_agencies=Agency.objects.count(),
        total_fees=FOIARequest.objects.aggregate(Sum('price'))['price__sum'],
        )
    # stats needs to be saved before many to many relationships can be set
    stats.users_today = User.objects.filter(last_login__year=yesterday.year,
                                            last_login__month=yesterday.month,
                                            last_login__day=yesterday.day)
    stats.save()
