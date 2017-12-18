"""
Tasks for the account application
"""

from celery.schedules import crontab
from celery.task import periodic_task
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db.models import Count, F, Q, Sum

from datetime import date, timedelta
import logging
import os
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal

from muckrock.accounts.models import Profile, Statistics
from muckrock.agency.models import Agency
from muckrock.communication.models import (
        EmailCommunication,
        FaxCommunication,
        MailCommunication,
        PortalCommunication,
        )
from muckrock.crowdfund.models import Crowdfund, CrowdfundPayment
from muckrock.foia.models import FOIARequest, FOIAFile, FOIACommunication
from muckrock.foiamachine.models import FoiaMachineRequest
from muckrock.jurisdiction.models import (
        Exemption,
        InvokedExemption,
        ExampleAppeal,
        )
from muckrock.models import ExtractDay, Now
from muckrock.news.models import Article
from muckrock.organization.models import Organization
from muckrock.project.models import Project
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
        CrowdfundTask,
        FailedFaxTask,
        ReviewAgencyTask,
        PortalTask,
        )

logger = logging.getLogger(__name__)

client = Client(os.environ.get('SENTRY_DSN'))
register_logger_signal(client)
register_signal(client)

@periodic_task(run_every=crontab(hour=0, minute=30),
    name='muckrock.accounts.tasks.store_statistics')
def store_statistics():
    """Store the daily statistics"""

    yesterday = date.today() - timedelta(1)

    stats = Statistics.objects.create(
        date=yesterday,
        total_requests=FOIARequest.objects.count(),
        total_requests_success=
            FOIARequest.objects.filter(status='done').count(),
        total_requests_denied=
            FOIARequest.objects.filter(status='rejected').count(),
        total_requests_draft=
            FOIARequest.objects.filter(status='started').count(),
        total_requests_submitted=
            FOIARequest.objects.filter(status='submitted').count(),
        total_requests_awaiting_ack=
            FOIARequest.objects.filter(status='ack').count(),
        total_requests_awaiting_response=
            FOIARequest.objects.filter(status='processed').count(),
        total_requests_awaiting_appeal=
            FOIARequest.objects.filter(status='appealing').count(),
        total_requests_fix_required=
            FOIARequest.objects.filter(status='fix').count(),
        total_requests_payment_required=
            FOIARequest.objects.filter(status='payment').count(),
        total_requests_no_docs=
            FOIARequest.objects.filter(status='no_docs').count(),
        total_requests_partial=
            FOIARequest.objects.filter(status='partial').count(),
        total_requests_abandoned=
            FOIARequest.objects.filter(status='abandoned').count(),
        total_requests_lawsuit=
            FOIARequest.objects.filter(status='lawsuit').count(),
        requests_processing_days=(FOIARequest.objects
            .filter(status='submitted')
            .exclude(date_processing=None)
            .aggregate(days=Sum(date.today() - F('date_processing')))['days']),
        sent_communications_portal=PortalCommunication.objects
            .filter(
                communication__date__range=(yesterday, date.today()),
                communication__response=False,
                ).count(),
        sent_communications_email=EmailCommunication.objects
            .filter(
                communication__date__range=(yesterday, date.today()),
                communication__response=False,
                ).count(),
        sent_communications_fax=FaxCommunication.objects
            .filter(
                communication__date__range=(yesterday, date.today()),
                communication__response=False,
                ).count(),
        sent_communications_mail=MailCommunication.objects
            .filter(
                communication__date__range=(yesterday, date.today()),
                communication__response=False,
                ).count(),
        machine_requests=
            FoiaMachineRequest.objects.count(),
        machine_requests_success=
            FoiaMachineRequest.objects.filter(status='done').count(),
        machine_requests_denied=
            FoiaMachineRequest.objects.filter(status='rejected').count(),
        machine_requests_draft=
            FoiaMachineRequest.objects.filter(status='started').count(),
        machine_requests_submitted=
            FoiaMachineRequest.objects.filter(status='submitted').count(),
        machine_requests_awaiting_ack=
            FoiaMachineRequest.objects.filter(status='ack').count(),
        machine_requests_awaiting_response=
            FoiaMachineRequest.objects.filter(status='processed').count(),
        machine_requests_awaiting_appeal=
            FoiaMachineRequest.objects.filter(status='appealing').count(),
        machine_requests_fix_required=
            FoiaMachineRequest.objects.filter(status='fix').count(),
        machine_requests_payment_required=
            FoiaMachineRequest.objects.filter(status='payment').count(),
        machine_requests_no_docs=
            FoiaMachineRequest.objects.filter(status='no_docs').count(),
        machine_requests_partial=
            FoiaMachineRequest.objects.filter(status='partial').count(),
        machine_requests_abandoned=
            FoiaMachineRequest.objects.filter(status='abandoned').count(),
        machine_requests_lawsuit=
            FoiaMachineRequest.objects.filter(status='lawsuit').count(),
        total_pages=FOIAFile.objects.aggregate(Sum('pages'))['pages__sum'],
        total_users=User.objects.count(),
        total_users_excluding_agencies=
            User.objects.exclude(profile__acct_type='agency').count(),
        total_users_filed=User.objects.annotate(
                num_foia=Count('foiarequest')
        ).exclude(
                num_foia=0,
        ).count(),
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
        daily_articles=Article.objects.filter(
                pub_date__gte=yesterday, pub_date__lt=date.today()).count(),
        orphaned_communications=
            FOIACommunication.objects.filter(foia=None).count(),
        stale_agencies=Agency.objects.filter(stale=True).count(),
        unapproved_agencies=Agency.objects.filter(status='pending').count(),
        portal_agencies=Agency.objects.exclude(portal=None).count(),
        total_tasks=Task.objects.count(),
        total_unresolved_tasks=Task.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_tasks=Task.objects.get_deferred().count(),
        total_generic_tasks=GenericTask.objects.count(),
        total_unresolved_generic_tasks=
            GenericTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_generic_tasks=
            GenericTask.objects.get_deferred().count(),
        total_orphan_tasks=OrphanTask.objects.count(),
        total_unresolved_orphan_tasks=
            OrphanTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_orphan_tasks=
            OrphanTask.objects.get_deferred().count(),
        total_snailmail_tasks=SnailMailTask.objects.count(),
        total_unresolved_snailmail_tasks=
            SnailMailTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_snailmail_tasks=
            SnailMailTask.objects.get_deferred().count(),
        total_rejected_tasks=RejectedEmailTask.objects.count(),
        total_unresolved_rejected_tasks=
            RejectedEmailTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_rejected_tasks=
            RejectedEmailTask.objects.get_deferred().count(),
        total_staleagency_tasks=StaleAgencyTask.objects.count(),
        total_unresolved_staleagency_tasks=
            StaleAgencyTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_staleagency_tasks=
            StaleAgencyTask.objects.get_deferred().count(),
        total_flagged_tasks=FlaggedTask.objects.count(),
        total_unresolved_flagged_tasks=
            FlaggedTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_flagged_tasks=
            FlaggedTask.objects.get_deferred().count(),
        total_newagency_tasks=NewAgencyTask.objects.count(),
        total_unresolved_newagency_tasks=
            NewAgencyTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_newagency_tasks=
            NewAgencyTask.objects.get_deferred().count(),
        total_response_tasks=ResponseTask.objects.count(),
        total_unresolved_response_tasks=
            ResponseTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_response_tasks=
            ResponseTask.objects.get_deferred().count(),
        total_faxfail_tasks=FailedFaxTask.objects.count(),
        total_unresolved_faxfail_tasks=
            FailedFaxTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_faxfail_tasks=
            FailedFaxTask.objects.get_deferred().count(),
        total_crowdfundpayment_tasks=CrowdfundTask.objects.count(),
        total_unresolved_crowdfundpayment_tasks=
            CrowdfundTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_crowdfundpayment_tasks=
            CrowdfundTask.objects.get_deferred().count(),
        total_reviewagency_tasks=ReviewAgencyTask.objects.count(),
        total_unresolved_reviewagency_tasks=
            ReviewAgencyTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_reviewagency_tasks=
            ReviewAgencyTask.objects.get_deferred().count(),
        total_portal_tasks=PortalTask.objects.count(),
        total_unresolved_portal_tasks=
            PortalTask.objects.filter(resolved=False).get_undeferred().count(),
        total_deferred_portal_tasks=
            PortalTask.objects.get_deferred().count(),
        daily_robot_response_tasks=ResponseTask.objects.filter(
               date_done__gte=yesterday,
               date_done__lt=date.today(),
               resolved_by__profile__acct_type='robot',
               ).count(),
        flag_processing_days=(FlaggedTask.objects
            .exclude(resolved=True)
            .get_undeferred()
            .aggregate(days=ExtractDay(Sum(Now() - F('date_created'))))['days']),
        unresolved_snailmail_appeals=
            SnailMailTask.objects
            .filter(resolved=False, category='a')
            .get_undeferred()
            .count(),
        total_active_org_members=Profile.objects.filter(
                organization__active=True,
                organization__monthly_cost__gt=0,
                ).count(),
        total_active_orgs=Organization.objects.filter(
                active=True,
                monthly_cost__gt=0,
                ).count(),
        total_crowdfunds=Crowdfund.objects.count(),
        total_crowdfunds_pro=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='pro') |
                Q(projects__contributors__profile__acct_type='pro')
                ).count(),
        total_crowdfunds_basic=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='basic') |
                Q(projects__contributors__profile__acct_type='basic')
                ).count(),
        total_crowdfunds_beta=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='beta') |
                Q(projects__contributors__profile__acct_type='beta')
                ).count(),
        total_crowdfunds_proxy=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='proxy') |
                Q(projects__contributors__profile__acct_type='proxy')
                ).count(),
        total_crowdfunds_admin=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='admin') |
                Q(projects__contributors__profile__acct_type='admin')
                ).count(),
        open_crowdfunds=Crowdfund.objects.filter(closed=False).count(),
        open_crowdfunds_pro=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='pro') |
                Q(projects__contributors__profile__acct_type='pro'),
                closed=False,
                ).count(),
        open_crowdfunds_basic=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='basic') |
                Q(projects__contributors__profile__acct_type='basic'),
                closed=False,
                ).count(),
        open_crowdfunds_beta=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='beta') |
                Q(projects__contributors__profile__acct_type='beta'),
                closed=False,
                ).count(),
        open_crowdfunds_proxy=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='proxy') |
                Q(projects__contributors__profile__acct_type='proxy'),
                closed=False,
                ).count(),
        open_crowdfunds_admin=Crowdfund.objects.filter(
                Q(foia__user__profile__acct_type='admin') |
                Q(projects__contributors__profile__acct_type='admin'),
                closed=False,
                ).count(),
        closed_crowdfunds_0=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent=0)
            .count(),
        closed_crowdfunds_0_25=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=0, percent__lte=0.25)
            .count(),
        closed_crowdfunds_25_50=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=0.25, percent__lte=0.50)
            .count(),
        closed_crowdfunds_50_75=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=0.50, percent__lte=0.75)
            .count(),
        closed_crowdfunds_75_100=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=0.75, percent__lte=1.00)
            .count(),
        closed_crowdfunds_100_125=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=1.00, percent__lte=1.25)
            .count(),
        closed_crowdfunds_125_150=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=1.25, percent__lte=1.50)
            .count(),
        closed_crowdfunds_150_175=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=1.50, percent__lte=1.75)
            .count(),
        closed_crowdfunds_175_200=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=1.75, percent__lte=2.00)
            .count(),
        closed_crowdfunds_200=Crowdfund.objects
            .annotate(percent=F('payment_received') / F('payment_required'))
            .filter(closed=True, percent__gt=2.00)
            .count(),
        total_crowdfund_payments=CrowdfundPayment.objects.count(),
        total_crowdfund_payments_loggedin=CrowdfundPayment.objects
            .exclude(user=None).count(),
        total_crowdfund_payments_loggedout=CrowdfundPayment.objects
            .filter(user=None).count(),
        public_projects=Project.objects
            .filter(private=False, approved=True).count(),
        private_projects=Project.objects
            .filter(private=True, approved=True).count(),
        unapproved_projects=Project.objects.filter(approved=False).count(),
        crowdfund_projects=Project.objects.exclude(crowdfunds=None).count(),
        project_users=User.objects.exclude(projects=None).count(),
        project_users_pro=User.objects
            .filter(profile__acct_type='pro').exclude(projects=None).count(),
        project_users_basic=User.objects
            .filter(profile__acct_type='basic').exclude(projects=None).count(),
        project_users_beta=User.objects
            .filter(profile__acct_type='beta').exclude(projects=None).count(),
        project_users_proxy=User.objects
            .filter(profile__acct_type='proxy').exclude(projects=None).count(),
        project_users_admin=User.objects
            .filter(profile__acct_type='admin').exclude(projects=None).count(),
        total_exemptions=Exemption.objects.count(),
        total_invoked_exemptions=InvokedExemption.objects.count(),
        total_example_appeals=ExampleAppeal.objects.count(),
        )
    # stats needs to be saved before many to many relationships can be set
    stats.users_today = User.objects.filter(last_login__year=yesterday.year,
                                            last_login__month=yesterday.month,
                                            last_login__day=yesterday.day)
    stats.save()

@periodic_task(run_every=crontab(day_of_week='sun', hour=1, minute=0),
               name='muckrock.accounts.tasks.db_cleanup')
def db_cleanup():
    """Call some management commands to clean up the database"""
    call_command('deleterevisions', 'foia', days=180,
            force=True, confirmation=False, verbosity=2)
    call_command('deleterevisions', 'task', days=180,
            force=True, confirmation=False, verbosity=2)
    call_command('deleterevisions', days=730,
            force=True, confirmation=False, verbosity=2)
    call_command('clearsessions', verbosity=2)
