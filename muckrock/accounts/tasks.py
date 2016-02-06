
"""
Tasks for the account application
"""

from celery.schedules import crontab
from celery.task import periodic_task
from django.contrib.auth.models import User
from django.db.models import Sum, F

import logging
from datetime import date, timedelta

from muckrock.accounts.models import Profile, Statistics
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIAFile, FOIACommunication
from muckrock.news.models import Article
from muckrock.task.models import (
        Task,
        OrphanTask,
        SnailMailTask,
        RejectedEmailTask,
        StaleAgencyTask,
        FlaggedTask,
        NewAgencyTask,
        ResponseTask,
        GenericTask,
        PaymentTask,
        GenericCrowdfundTask,
        FailedFaxTask,
        )

logger = logging.getLogger(__name__)

@periodic_task(run_every=crontab(hour=0, minute=30), name='muckrock.accounts.tasks.store_statstics')
def store_statstics():
    """Store the daily statistics"""

    yesterday = date.today() - timedelta(1)

    stats = Statistics.objects.create(
        date=yesterday,
        total_requests=FOIARequest.objects.count(),
        total_requests_success=FOIARequest.objects.filter(status='done').count(),
        total_requests_denied=FOIARequest.objects.filter(status='rejected').count(),
        total_requests_draft=FOIARequest.objects.filter(status='started').count(),
        total_requests_submitted=FOIARequest.objects.filter(status='submitted').count(),
        total_requests_awaiting_ack=FOIARequest.objects.filter(status='ack').count(),
        total_requests_awaiting_response=FOIARequest.objects.filter(status='processed').count(),
        total_requests_awaiting_appeal=FOIARequest.objects.filter(status='appealing').count(),
        total_requests_fix_required=FOIARequest.objects.filter(status='fix').count(),
        total_requests_payment_required=FOIARequest.objects.filter(status='payment').count(),
        total_requests_no_docs=FOIARequest.objects.filter(status='no_docs').count(),
        total_requests_partial=FOIARequest.objects.filter(status='partial').count(),
        total_requests_abandoned=FOIARequest.objects.filter(status='abandoned').count(),
        requests_processing_days=(FOIARequest.objects
            .filter(status='submitted')
            .exclude(date_processing=None)
            .aggregate(days=Sum(date.today() - F('date_processing')))['days']),
        total_pages=FOIAFile.objects.aggregate(Sum('pages'))['pages__sum'],
        total_users=User.objects.count(),
        total_agencies=Agency.objects.count(),
        total_fees=FOIARequest.objects.aggregate(Sum('price'))['price__sum'],
        pro_users=Profile.objects.filter(acct_type='pro').count(),
        pro_user_names=';'.join(p.user.username for p in Profile.objects.filter(acct_type='pro')),
        daily_requests_pro=FOIARequest.objects.filter(
            user__profile__acct_type='pro',
            date_submitted=yesterday
        ).exclude(
            user__profile__organization__active=True,
            user__profile__organization__monthly_cost__gt=0,
        ).count(),
        daily_requests_basic=FOIARequest.objects.filter(
            user__profile__acct_type='basic',
            date_submitted=yesterday
        ).exclude(
            user__profile__organization__active=True,
            user__profile__organization__monthly_cost__gt=0,
        ).count(),
        daily_requests_beta=FOIARequest.objects.filter(
            user__profile__acct_type='beta',
            date_submitted=yesterday
        ).exclude(
            user__profile__organization__active=True,
            user__profile__organization__monthly_cost__gt=0,
        ).count(),
        daily_requests_proxy=FOIARequest.objects.filter(
            user__profile__acct_type='proxy',
            date_submitted=yesterday
        ).exclude(
            user__profile__organization__active=True,
            user__profile__organization__monthly_cost__gt=0,
        ).count(),
        daily_requests_admin=FOIARequest.objects.filter(
            user__profile__acct_type='admin',
            date_submitted=yesterday
        ).exclude(
            user__profile__organization__active=True,
            user__profile__organization__monthly_cost__gt=0,
        ).count(),
        daily_requests_org=FOIARequest.objects.filter(
            user__profile__organization__active=True,
            user__profile__organization__monthly_cost__gt=0,
            date_submitted=yesterday
        ).count(),
        daily_articles=Article.objects.filter(pub_date__gte=yesterday,
                                              pub_date__lt=date.today()).count(),
        orphaned_communications=FOIACommunication.objects.filter(foia=None).count(),
        stale_agencies=Agency.objects.filter(stale=True).count(),
        unapproved_agencies=Agency.objects.filter(approved=False).count(),
        total_tasks=Task.objects.count(),
        total_unresolved_tasks=Task.objects.filter(resolved=False).count(),
        total_generic_tasks=GenericTask.objects.count(),
        total_unresolved_generic_tasks=GenericTask.objects.filter(resolved=False).count(),
        total_orphan_tasks=OrphanTask.objects.count(),
        total_unresolved_orphan_tasks=OrphanTask.objects.filter(resolved=False).count(),
        total_snailmail_tasks=SnailMailTask.objects.count(),
        total_unresolved_snailmail_tasks=SnailMailTask.objects.filter(resolved=False).count(),
        total_rejected_tasks=RejectedEmailTask.objects.count(),
        total_unresolved_rejected_tasks=
            RejectedEmailTask.objects.filter(resolved=False).count(),
        total_staleagency_tasks=StaleAgencyTask.objects.count(),
        total_unresolved_staleagency_tasks=StaleAgencyTask.objects.filter(resolved=False).count(),
        total_flagged_tasks=FlaggedTask.objects.count(),
        total_unresolved_flagged_tasks=FlaggedTask.objects.filter(resolved=False).count(),
        total_newagency_tasks=NewAgencyTask.objects.count(),
        total_unresolved_newagency_tasks=NewAgencyTask.objects.filter(resolved=False).count(),
        total_response_tasks=ResponseTask.objects.count(),
        total_unresolved_response_tasks=ResponseTask.objects.filter(resolved=False).count(),
        total_faxfail_tasks=FailedFaxTask.objects.count(),
        total_unresolved_faxfail_tasks=FailedFaxTask.objects.filter(resolved=False).count(),
        total_payment_tasks=PaymentTask.objects.count(),
        total_unresolved_payment_tasks=PaymentTask.objects.filter(resolved=False).count(),
        total_crowdfundpayment_tasks=GenericCrowdfundTask.objects.count(),
        total_unresolved_crowdfundpayment_tasks=
            GenericCrowdfundTask.objects.filter(resolved=False).count(),
        daily_robot_response_tasks=ResponseTask.objects.filter(
               date_done__gte=yesterday,
               date_done__lt=date.today(),
               resolved_by__profile__acct_type='robot',
               ).count(),
        total_active_org_members = Profile.objects.filter(
                organization__active=True,
                organization__monthly_cost__gt=0,
                ).count(),
        total_active_orgs = Organization.objects.filter(
                active=True,
                monthly_cost__gt=0,
                ).count(),
        )
    # stats needs to be saved before many to many relationships can be set
    stats.users_today = User.objects.filter(last_login__year=yesterday.year,
                                            last_login__month=yesterday.month,
                                            last_login__day=yesterday.day)
    stats.save()

def _notices(email_pref):
    """Send out notices"""
    profiles_to_notify = Profile.objects.filter(email_pref=email_pref).distinct()
    for profile in profiles_to_notify:
        profile.send_notifications()

@periodic_task(run_every=crontab(day_of_week='mon', hour=10, minute=0),
               name='muckrock.accounts.tasks.weekly')
def weekly_notices():
    """Send out weekly notices"""
    _notices('weekly')
