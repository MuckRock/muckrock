"""
Tasks for the account application
"""

# Django
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from celery.task import periodic_task
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models import Count, F, Sum
from django.utils import timezone

# Standard Library
import logging
import os
from datetime import date, datetime, time, timedelta

# Third Party
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal

# MuckRock
from muckrock.accounts.models import Statistics
from muckrock.agency.models import Agency
from muckrock.communication.models import (
    EmailCommunication,
    FaxCommunication,
    MailCommunication,
    PortalCommunication,
)
from muckrock.crowdfund.models import Crowdfund, CrowdfundPayment
from muckrock.crowdsource.models import Crowdsource, CrowdsourceResponse
from muckrock.foia.models import FOIACommunication, FOIAComposer, FOIAFile, FOIARequest
from muckrock.foiamachine.models import FoiaMachineRequest
from muckrock.jurisdiction.models import ExampleAppeal, Exemption, InvokedExemption
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.task.models import (
    CrowdfundTask,
    FailedFaxTask,
    FlaggedTask,
    NewAgencyTask,
    OrphanTask,
    PortalTask,
    RejectedEmailTask,
    ResponseTask,
    ReviewAgencyTask,
    SnailMailTask,
    Task,
)

logger = logging.getLogger(__name__)

client = Client(os.environ.get("SENTRY_DSN"))
register_logger_signal(client)
register_signal(client)


@periodic_task(
    run_every=crontab(hour=0, minute=30),
    name="muckrock.accounts.tasks.store_statistics",
)
def store_statistics():
    """Store the daily statistics"""
    # pylint: disable=too-many-statements

    midnight = time(tzinfo=timezone.get_current_timezone())
    today_midnight = datetime.combine(date.today(), midnight)
    yesterday = date.today() - timedelta(1)
    yesterday_midnight = today_midnight - timedelta(1)

    kwargs = {}
    kwargs["date"] = yesterday
    kwargs["total_requests"] = FOIARequest.objects.count()
    kwargs["total_requests_success"] = FOIARequest.objects.filter(status="done").count()
    kwargs["total_requests_denied"] = FOIARequest.objects.filter(
        status="rejected"
    ).count()
    kwargs["total_requests_draft"] = 0  # draft is no longer a valid status
    kwargs["total_requests_submitted"] = FOIARequest.objects.filter(
        status="submitted"
    ).count()
    kwargs["total_requests_awaiting_ack"] = FOIARequest.objects.filter(
        status="ack"
    ).count()
    kwargs["total_requests_awaiting_response"] = FOIARequest.objects.filter(
        status="processed"
    ).count()
    kwargs["total_requests_awaiting_appeal"] = FOIARequest.objects.filter(
        status="appealing"
    ).count()
    kwargs["total_requests_fix_required"] = FOIARequest.objects.filter(
        status="fix"
    ).count()
    kwargs["total_requests_payment_required"] = FOIARequest.objects.filter(
        status="payment"
    ).count()
    kwargs["total_requests_no_docs"] = FOIARequest.objects.filter(
        status="no_docs"
    ).count()
    kwargs["total_requests_partial"] = FOIARequest.objects.filter(
        status="partial"
    ).count()
    kwargs["total_requests_abandoned"] = FOIARequest.objects.filter(
        status="abandoned"
    ).count()
    kwargs["total_requests_lawsuit"] = FOIARequest.objects.filter(
        status="lawsuit"
    ).count()
    kwargs["requests_processing_days"] = FOIARequest.objects.get_processing_days()
    kwargs["total_composers"] = FOIAComposer.objects.count()
    kwargs["total_composers_draft"] = FOIAComposer.objects.filter(
        status="started"
    ).count()
    kwargs["total_composers_submitted"] = FOIAComposer.objects.filter(
        status="submitted"
    ).count()
    kwargs["total_composers_filed"] = FOIAComposer.objects.filter(
        status="filed"
    ).count()
    kwargs["sent_communications_portal"] = PortalCommunication.objects.filter(
        communication__datetime__range=(yesterday_midnight, today_midnight),
        communication__response=False,
    ).count()
    kwargs["sent_communications_email"] = EmailCommunication.objects.filter(
        communication__datetime__range=(yesterday_midnight, today_midnight),
        communication__response=False,
    ).count()
    kwargs["sent_communications_fax"] = FaxCommunication.objects.filter(
        communication__datetime__range=(yesterday_midnight, today_midnight),
        communication__response=False,
    ).count()
    kwargs["sent_communications_mail"] = MailCommunication.objects.filter(
        communication__datetime__range=(yesterday_midnight, today_midnight),
        communication__response=False,
    ).count()
    kwargs["machine_requests"] = FoiaMachineRequest.objects.count()
    kwargs["machine_requests_success"] = FoiaMachineRequest.objects.filter(
        status="done"
    ).count()
    kwargs["machine_requests_denied"] = FoiaMachineRequest.objects.filter(
        status="rejected"
    ).count()
    kwargs["machine_requests_draft"] = FoiaMachineRequest.objects.filter(
        status="started"
    ).count()
    kwargs["machine_requests_submitted"] = FoiaMachineRequest.objects.filter(
        status="submitted"
    ).count()
    kwargs["machine_requests_awaiting_ack"] = FoiaMachineRequest.objects.filter(
        status="ack"
    ).count()
    kwargs["machine_requests_awaiting_response"] = FoiaMachineRequest.objects.filter(
        status="processed"
    ).count()
    kwargs["machine_requests_awaiting_appeal"] = FoiaMachineRequest.objects.filter(
        status="appealing"
    ).count()
    kwargs["machine_requests_fix_required"] = FoiaMachineRequest.objects.filter(
        status="fix"
    ).count()
    kwargs["machine_requests_payment_required"] = FoiaMachineRequest.objects.filter(
        status="payment"
    ).count()
    kwargs["machine_requests_no_docs"] = FoiaMachineRequest.objects.filter(
        status="no_docs"
    ).count()
    kwargs["machine_requests_partial"] = FoiaMachineRequest.objects.filter(
        status="partial"
    ).count()
    kwargs["machine_requests_abandoned"] = FoiaMachineRequest.objects.filter(
        status="abandoned"
    ).count()
    kwargs["machine_requests_lawsuit"] = FoiaMachineRequest.objects.filter(
        status="lawsuit"
    ).count()
    kwargs["total_pages"] = FOIAFile.objects.aggregate(Sum("pages"))["pages__sum"]
    # user stats will now be kept on squarelet
    kwargs["total_users"] = 0
    kwargs["total_users_excluding_agencies"] = 0
    kwargs["total_users_filed"] = (
        User.objects.annotate(num_foia=Count("composers")).exclude(num_foia=0).count()
    )  # this is still on muckrock since it deals with foia composers
    kwargs["total_agencies"] = Agency.objects.count()
    kwargs["total_fees"] = FOIARequest.objects.aggregate(Sum("price"))["price__sum"]
    kwargs["pro_users"] = 0  # squarelet
    kwargs["pro_user_names"] = ""  # squarelet
    kwargs["daily_requests_pro"] = (
        FOIARequest.objects.filter(
            composer__organization__entitlement__slug="professional"
        )
        .get_submitted_range(yesterday_midnight, today_midnight)
        .exclude_org_users()
        .count()
    )
    kwargs["daily_requests_basic"] = (
        FOIARequest.objects.filter(composer__organization__entitlement__slug="free")
        .get_submitted_range(yesterday_midnight, today_midnight)
        .exclude_org_users()
        .count()
    )
    kwargs["daily_requests_beta"] = (
        FOIARequest.objects.filter(composer__organization__entitlement__slug="beta")
        .get_submitted_range(yesterday_midnight, today_midnight)
        .exclude_org_users()
        .count()
    )
    kwargs["daily_requests_proxy"] = (
        FOIARequest.objects.filter(composer__organization__entitlement__slug="proxy")
        .get_submitted_range(yesterday_midnight, today_midnight)
        .exclude_org_users()
        .count()
    )
    kwargs["daily_requests_admin"] = (
        FOIARequest.objects.filter(composer__organization__entitlement__slug="admin")
        .get_submitted_range(yesterday_midnight, today_midnight)
        .exclude_org_users()
        .count()
    )
    kwargs["daily_requests_org"] = (
        FOIARequest.objects.filter(
            composer__organization__entitlement__slug="organization"
        )
        .get_submitted_range(yesterday_midnight, today_midnight)
        .count()
    )
    kwargs["daily_requests_other"] = (
        FOIARequest.objects.exclude(
            composer__organization__entitlement__slug__in=[
                "professional",
                "free",
                "beta",
                "proxy",
                "admin",
                "organization",
            ]
        )
        .get_submitted_range(yesterday_midnight, today_midnight)
        .count()
    )
    kwargs["daily_articles"] = Article.objects.filter(
        pub_date__range=(yesterday_midnight, today_midnight)
    ).count()
    kwargs["orphaned_communications"] = FOIACommunication.objects.filter(
        foia=None
    ).count()
    kwargs["stale_agencies"] = 0  # stake agencies no longer exist
    kwargs["unapproved_agencies"] = Agency.objects.filter(status="pending").count()
    kwargs["portal_agencies"] = Agency.objects.exclude(portal=None).count()
    kwargs["total_tasks"] = Task.objects.count()
    kwargs["total_unresolved_tasks"] = (
        Task.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs["total_deferred_tasks"] = Task.objects.get_deferred().count()
    # we no longer use generic tasks
    kwargs["total_generic_tasks"] = 0
    kwargs["total_unresolved_generic_tasks"] = 0
    kwargs["total_deferred_generic_tasks"] = 0
    kwargs["total_orphan_tasks"] = OrphanTask.objects.count()
    kwargs["total_unresolved_orphan_tasks"] = (
        OrphanTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs["total_deferred_orphan_tasks"] = OrphanTask.objects.get_deferred().count()
    kwargs["total_snailmail_tasks"] = SnailMailTask.objects.count()
    kwargs["total_unresolved_snailmail_tasks"] = (
        SnailMailTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs[
        "total_deferred_snailmail_tasks"
    ] = SnailMailTask.objects.get_deferred().count()
    kwargs["total_rejected_tasks"] = RejectedEmailTask.objects.count()
    kwargs["total_unresolved_rejected_tasks"] = (
        RejectedEmailTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs[
        "total_deferred_rejected_tasks"
    ] = RejectedEmailTask.objects.get_deferred().count()
    kwargs["total_staleagency_tasks"] = 0
    kwargs["total_unresolved_staleagency_tasks"] = 0
    kwargs["total_deferred_staleagency_tasks"] = 0
    kwargs["total_flagged_tasks"] = FlaggedTask.objects.count()
    kwargs["total_unresolved_flagged_tasks"] = (
        FlaggedTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs["total_deferred_flagged_tasks"] = FlaggedTask.objects.get_deferred().count()
    kwargs["total_newagency_tasks"] = NewAgencyTask.objects.count()
    kwargs["total_unresolved_newagency_tasks"] = (
        NewAgencyTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs[
        "total_deferred_newagency_tasks"
    ] = NewAgencyTask.objects.get_deferred().count()
    kwargs["total_response_tasks"] = ResponseTask.objects.count()
    kwargs["total_unresolved_response_tasks"] = (
        ResponseTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs[
        "total_deferred_response_tasks"
    ] = ResponseTask.objects.get_deferred().count()
    kwargs["total_faxfail_tasks"] = FailedFaxTask.objects.count()
    kwargs["total_unresolved_faxfail_tasks"] = (
        FailedFaxTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs[
        "total_deferred_faxfail_tasks"
    ] = FailedFaxTask.objects.get_deferred().count()
    kwargs["total_crowdfundpayment_tasks"] = CrowdfundTask.objects.count()
    kwargs["total_unresolved_crowdfundpayment_tasks"] = (
        CrowdfundTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs[
        "total_deferred_crowdfundpayment_tasks"
    ] = CrowdfundTask.objects.get_deferred().count()
    kwargs["total_reviewagency_tasks"] = ReviewAgencyTask.objects.count()
    kwargs["total_unresolved_reviewagency_tasks"] = (
        ReviewAgencyTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs[
        "total_deferred_reviewagency_tasks"
    ] = ReviewAgencyTask.objects.get_deferred().count()
    kwargs["total_portal_tasks"] = PortalTask.objects.count()
    kwargs["total_unresolved_portal_tasks"] = (
        PortalTask.objects.filter(resolved=False).get_undeferred().count()
    )
    kwargs["total_deferred_portal_tasks"] = PortalTask.objects.get_deferred().count()
    kwargs["daily_robot_response_tasks"] = ResponseTask.objects.filter(
        date_done__gte=yesterday_midnight,
        date_done__lt=today_midnight,
        resolved_by__username="mlrobot",
    ).count()
    kwargs["flag_processing_days"] = FlaggedTask.objects.get_processing_days()
    kwargs["unresolved_snailmail_appeals"] = (
        SnailMailTask.objects.filter(resolved=False, category="a")
        .get_undeferred()
        .count()
    )
    # squarelet
    kwargs["total_active_org_members"] = 0
    kwargs["total_active_orgs"] = 0
    kwargs["total_crowdfunds"] = Crowdfund.objects.count()
    kwargs["total_crowdfunds_pro"] = Crowdfund.objects.filter_by_entitlement(
        "professional"
    ).count()
    kwargs["total_crowdfunds_basic"] = Crowdfund.objects.filter_by_entitlement(
        "free"
    ).count()
    kwargs["total_crowdfunds_beta"] = Crowdfund.objects.filter_by_entitlement(
        "beta"
    ).count()
    kwargs["total_crowdfunds_proxy"] = Crowdfund.objects.filter_by_entitlement(
        "proxy"
    ).count()
    kwargs["total_crowdfunds_admin"] = Crowdfund.objects.filter_by_entitlement(
        "admin"
    ).count()
    kwargs["open_crowdfunds"] = Crowdfund.objects.filter(closed=False).count()
    kwargs["open_crowdfunds_pro"] = (
        Crowdfund.objects.filter_by_entitlement("professional")
        .filter(closed=False)
        .count()
    )
    kwargs["open_crowdfunds_basic"] = (
        Crowdfund.objects.filter_by_entitlement("free").filter(closed=False).count()
    )
    kwargs["open_crowdfunds_beta"] = (
        Crowdfund.objects.filter_by_entitlement("beta").filter(closed=False).count()
    )
    kwargs["open_crowdfunds_proxy"] = (
        Crowdfund.objects.filter_by_entitlement("proxy").filter(closed=False).count()
    )
    kwargs["open_crowdfunds_admin"] = (
        Crowdfund.objects.filter_by_entitlement("admin").filter(closed=False).count()
    )
    kwargs["closed_crowdfunds_0"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent=0)
        .count()
    )
    kwargs["closed_crowdfunds_0_25"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=0, percent__lte=0.25)
        .count()
    )
    kwargs["closed_crowdfunds_25_50"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=0.25, percent__lte=0.50)
        .count()
    )
    kwargs["closed_crowdfunds_50_75"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=0.50, percent__lte=0.75)
        .count()
    )
    kwargs["closed_crowdfunds_75_100"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=0.75, percent__lte=1.00)
        .count()
    )
    kwargs["closed_crowdfunds_100_125"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=1.00, percent__lte=1.25)
        .count()
    )
    kwargs["closed_crowdfunds_125_150"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=1.25, percent__lte=1.50)
        .count()
    )
    kwargs["closed_crowdfunds_150_175"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=1.50, percent__lte=1.75)
        .count()
    )
    kwargs["closed_crowdfunds_175_200"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=1.75, percent__lte=2.00)
        .count()
    )
    kwargs["closed_crowdfunds_200"] = (
        Crowdfund.objects.annotate(
            percent=F("payment_received") / F("payment_required")
        )
        .filter(closed=True, percent__gt=2.00)
        .count()
    )
    kwargs["total_crowdfund_payments"] = CrowdfundPayment.objects.count()
    kwargs["total_crowdfund_payments_loggedin"] = CrowdfundPayment.objects.exclude(
        user=None
    ).count()
    kwargs["total_crowdfund_payments_loggedout"] = CrowdfundPayment.objects.filter(
        user=None
    ).count()
    kwargs["public_projects"] = Project.objects.filter(
        private=False, approved=True
    ).count()
    kwargs["private_projects"] = Project.objects.filter(
        private=True, approved=True
    ).count()
    kwargs["unapproved_projects"] = Project.objects.filter(approved=False).count()
    kwargs["crowdfund_projects"] = Project.objects.exclude(crowdfunds=None).count()
    kwargs["project_users"] = User.objects.exclude(projects=None).count()
    kwargs["project_users_pro"] = (
        User.objects.filter(organizations__entitlement__slug="professional")
        .exclude(projects=None)
        .count()
    )
    kwargs["project_users_basic"] = (
        User.objects.filter(organizations__entitlement__slug="free")
        .exclude(projects=None)
        .count()
    )
    kwargs["project_users_beta"] = (
        User.objects.filter(organizations__entitlement__slug="beta")
        .exclude(projects=None)
        .count()
    )
    kwargs["project_users_proxy"] = (
        User.objects.filter(organizations__entitlement__slug="proxy")
        .exclude(projects=None)
        .count()
    )
    kwargs["project_users_admin"] = (
        User.objects.filter(organizations__entitlement__slug="admin")
        .exclude(projects=None)
        .count()
    )
    kwargs["total_exemptions"] = Exemption.objects.count()
    kwargs["total_invoked_exemptions"] = InvokedExemption.objects.count()
    kwargs["total_example_appeals"] = ExampleAppeal.objects.count()
    kwargs["total_crowdsources"] = Crowdsource.objects.count()
    kwargs["total_draft_crowdsources"] = Crowdsource.objects.filter(
        status="draft"
    ).count()
    kwargs["total_open_crowdsources"] = Crowdsource.objects.filter(
        status="open"
    ).count()
    kwargs["total_close_crowdsources"] = Crowdsource.objects.filter(
        status="close"
    ).count()
    kwargs[
        "num_crowdsource_responded_users"
    ] = CrowdsourceResponse.objects.get_user_count()
    kwargs["total_crowdsource_responses"] = CrowdsourceResponse.objects.count()
    kwargs["crowdsource_responses_pro"] = CrowdsourceResponse.objects.filter(
        user__organizations__entitlement__slug="professional"
    ).count()
    kwargs["crowdsource_responses_basic"] = CrowdsourceResponse.objects.filter(
        user__organizations__entitlement__slug="free"
    ).count()
    kwargs["crowdsource_responses_beta"] = CrowdsourceResponse.objects.filter(
        user__organizations__entitlement__slug="beta"
    ).count()
    kwargs["crowdsource_responses_proxy"] = CrowdsourceResponse.objects.filter(
        user__organizations__entitlement__slug="proxy"
    ).count()
    kwargs["crowdsource_responses_admin"] = CrowdsourceResponse.objects.filter(
        user__organizations__entitlement__slug="admin"
    ).count()

    Statistics.objects.create(**kwargs)


@periodic_task(
    run_every=crontab(day_of_week="sun", hour=1, minute=0),
    time_limit=1800,
    soft_time_limit=1740,
    name="muckrock.accounts.tasks.db_cleanup",
)
def db_cleanup():
    """Call some management commands to clean up the database"""
    step = 0
    try:
        call_command("deleterevisions", "foia", days=180, verbosity=2)
        step = 1
        call_command("deleterevisions", "task", days=180, verbosity=2)
        step = 2
        call_command("deleterevisions", days=730, verbosity=2)
        step = 3
        call_command("clearsessions", verbosity=2)
        step = 4
    except SoftTimeLimitExceeded:
        logger.error("DB Clean up took too long, step %s", step)
