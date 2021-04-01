"""
Detail view for a FOIA request
"""

# pylint: disable=too-many-lines

# Django
from celery import current_app
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

# Standard Library
import json
import logging
from datetime import timedelta
from heapq import merge
from hmac import compare_digest

# Third Party
from constance import config

# MuckRock
from muckrock.accounts.models import Notification
from muckrock.communication.models import Check, EmailCommunication, FaxCommunication
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.constants import COMPOSER_EDIT_DELAY
from muckrock.foia.exceptions import FoiaFormError
from muckrock.foia.forms import (
    ContactInfoForm,
    FOIAAccessForm,
    FOIAAdminFixForm,
    FOIAAgencyReplyForm,
    FOIAEmbargoForm,
    FOIAEstimatedCompletionDateForm,
    FOIANoteForm,
    RequestFeeForm,
    ResendForm,
    TrackingNumberForm,
)
from muckrock.foia.forms.comms import AgencyPasscodeForm
from muckrock.foia.models import (
    END_STATUS,
    STATUS,
    FOIACommunication,
    FOIAComposer,
    FOIAMultiRequest,
    FOIARequest,
)
from muckrock.foia.tasks import composer_delayed_submit, zip_request
from muckrock.foia.views import detail_actions
from muckrock.portal.forms import PortalForm
from muckrock.tags.models import Tag
from muckrock.task.models import Task

logger = logging.getLogger(__name__)

AGENCY_STATUS = [
    ("processed", "Further Response Coming"),
    ("fix", "Fix Required"),
    ("payment", "Payment Required"),
    ("rejected", "Rejected"),
    ("no_docs", "No Responsive Documents"),
    ("done", "Completed"),
    ("partial", "Partially Completed"),
]


class Detail(DetailView):
    """Details of a single FOIA request as well
    as handling post actions for the request"""

    model = FOIARequest
    context_object_name = "foia"

    def __init__(self, *args, **kwargs):
        self.foia = None
        self.agency_reply_form = FOIAAgencyReplyForm()
        self.agency_passcode_form = None
        self.admin_fix_form = None
        self.resend_forms = None
        self.fee_form = None
        self.valid_passcode = False
        super(Detail, self).__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        """Handle forms"""
        self.foia = self.get_object()
        self.admin_fix_form = FOIAAdminFixForm(
            prefix="admin_fix",
            request=self.request,
            foia=self.get_object(),
            initial={
                "subject": self.foia.default_subject(),
                "other_emails": self.foia.cc_emails.all(),
            },
        )
        self.resend_forms = {
            c.pk: ResendForm(prefix=str(c.pk)) for c in self.foia.communications.all()
        }
        self.fee_form = RequestFeeForm(
            user=self.request.user, initial={"amount": self.foia.get_stripe_amount()}
        )
        self.agency_passcode_form = AgencyPasscodeForm(foia=self.foia)
        if request.POST:
            try:
                return self.post(request)
            except FoiaFormError as exc:
                # if their is a form error, update the form, continue onto
                # the GET path and show the invalid form with errors displayed
                if exc.form_name == "resend_form":
                    if exc.comm_id:
                        self.resend_forms[exc.comm_id] = exc.form
                else:
                    setattr(self, exc.form_name, exc.form)
                return self.get(request, *args, **kwargs)

        return super(Detail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        # pylint: disable=unused-argument
        # pylint: disable=unsubscriptable-object
        # this is called twice in dispatch, so cache to not actually run twice
        if self.foia:
            return self.foia

        foia = get_object_or_404(
            FOIARequest.objects.select_related(
                "agency__jurisdiction__parent__parent",
                "agency__jurisdiction__law",
                "agency__jurisdiction__parent__law",
                "crowdfund",
                "composer__user__profile",
                "portal",
                "email",
                "fax",
                "address",
            ).prefetch_related(
                "tracking_ids",
                "cc_emails",
                Prefetch(
                    "communications",
                    FOIACommunication.objects.select_related(
                        "from_user__profile__agency"
                    ).preload_list(),
                ),
                Prefetch(
                    "communications__faxes",
                    FaxCommunication.objects.order_by("-sent_datetime"),
                    to_attr="reverse_faxes",
                ),
                Prefetch(
                    "communications__emails",
                    EmailCommunication.objects.exclude(rawemail=None),
                    to_attr="raw_emails",
                ),
            ),
            agency__jurisdiction__slug=self.kwargs["jurisdiction"],
            agency__jurisdiction__pk=self.kwargs["jidx"],
            slug=self.kwargs["slug"],
            pk=self.kwargs["idx"],
        )
        valid_access_key = (
            compare_digest(self.request.GET.get("key", ""), foia.access_key)
            and foia.access_key != ""
        )
        self.valid_passcode = self.request.session.get(f"foiapasscode:{foia.pk}")
        has_perm = foia.has_perm(self.request.user, "view")
        if not has_perm and not valid_access_key and not self.valid_passcode:
            raise Http404()
        return foia

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        # pylint: disable=too-many-statements, too-many-locals
        context = super(Detail, self).get_context_data(**kwargs)

        self._get_agency_context_data(context)
        self._get_permission_context_data(context)
        self._get_task_context_data(context)
        self._get_obj_context_data(context)
        self._get_date_context_data(context)
        self._get_config_context_data(context)
        self._get_revoke_context_data(context)
        self._get_form_context_data(context)

        return context

    def _get_permission_context_data(self, context):
        """Get context data about permissions"""

        context["user_can_edit"] = self.foia.has_perm(self.request.user, "change")
        user_can_embargo = self.foia.has_perm(self.request.user, "embargo")

        context["user_can_pay"] = (
            self.foia.has_perm(self.request.user, "pay")
            and self.foia.status == "payment"
        )
        context["embargo"] = {
            "show": user_can_embargo or self.foia.embargo,
            "edit": user_can_embargo,
            "add": user_can_embargo,
            "remove": context["user_can_edit"] and self.foia.embargo,
        }
        context["is_thankable"] = self.foia.has_perm(self.request.user, "thank")

    def _get_form_context_data(self, context):
        """Get context data about forms"""
        context["access_form"] = FOIAAccessForm()
        context["admin_fix_form"] = self.admin_fix_form
        context["agency_passcode_form"] = self.agency_passcode_form
        context["agency_reply_form"] = self.agency_reply_form
        context["appeal_contact_info_form"] = ContactInfoForm(
            foia=self.foia, appeal=True, prefix="appeal"
        )
        context["change_estimated_date"] = FOIAEstimatedCompletionDateForm(
            instance=self.foia
        )
        context["contact_info_form"] = ContactInfoForm(
            foia=self.foia, prefix="followup"
        )
        context["crowdfund_form"] = CrowdfundForm(
            initial={
                "name": "Crowdfund Request: %s" % str(self.foia),
                "description": "Help cover the request fees needed to free these docs!",
                "payment_required": self.foia.get_stripe_amount(),
                "date_due": timezone.now() + timedelta(30),
                "foia": self.foia,
            }
        )
        context["embargo_form"] = FOIAEmbargoForm(
            initial={
                "permanent_embargo": self.foia.permanent_embargo,
                "date_embargo": self.foia.date_embargo,
            }
        )
        context["fee_form"] = self.fee_form
        context["note_form"] = FOIANoteForm()
        context["portal_form"] = PortalForm(foia=self.foia)
        context["resend_forms"] = self.resend_forms
        context["tracking_id_form"] = TrackingNumberForm()

        # this data used in a form
        context["status_choices"] = [(k, v) for (k, v) in STATUS if k != "submitted"]
        context["user_actions"] = self.foia.user_actions(
            self.request.user, context["is_agency_user"]
        )

    def _get_task_context_data(self, context):
        """Get context data for tasks"""
        if context["user_can_edit"] or self.request.user.is_staff:
            all_tasks = Task.objects.filter_by_foia(self.foia, self.request.user)
            open_tasks = [task for task in all_tasks if not task.resolved]
            context["task_count"] = len(all_tasks)
            context["open_task_count"] = len(open_tasks)
            context["open_tasks"] = open_tasks
            context["asignees"] = (
                User.objects.filter(is_staff=True)
                .select_related("profile")
                .order_by("profile__full_name")
            )

    def _get_obj_context_data(self, context):
        """Get context data about related objects"""
        context["all_tags"] = Tag.objects.all()
        context["cc_emails"] = json.dumps([str(e) for e in self.foia.cc_emails.all()])
        context["files"] = self.foia.get_files().select_related("comm__foia")[:50]

        notes = [
            (n.datetime, "note", n)
            for n in self.foia.notes.select_related("author").all()
        ]
        checks = [
            (c.created_datetime, "check", c)
            for c in Check.objects.filter(communication__foia=self.foia)
            .select_related("user__profile")
            .prefetch_related("communication__mails__events")
        ]
        context["notes"] = [(t, v) for _, t, v in merge(notes, checks)]

    def _get_date_context_data(self, context):
        """Get context data about dates"""
        context["past_due"] = (
            self.foia.date_due < timezone.now().date() if self.foia.date_due else False
        )
        context["embargo_needs_date"] = self.foia.status in END_STATUS
        context["show_estimated_date"] = self.foia.status not in [
            "submitted",
            "ack",
            "done",
            "rejected",
        ]

    def _get_config_context_data(self, context):
        """Get context data for configuration or administrative data"""

        context["sidebar_admin_url"] = reverse(
            "admin:foia_foiarequest_change", args=(self.foia.pk,)
        )
        if self.request.user.is_authenticated or context["is_agency_user"]:
            context["foia_cache_timeout"] = 0
        else:
            context["foia_cache_timeout"] = settings.DEFAULT_CACHE_TIMEOUT
        context["meta_noindex"] = self.foia.noindex
        context["enable_followup"] = config.ENABLE_FOLLOWUP
        context["disabled_followup_message"] = config.DISABLED_FOLLOWUP_MESSAGE

    def _get_revoke_context_data(self, context):
        """Get context data about revoking the request"""
        if (
            self.foia.composer.status == "submitted"
            and self.foia.composer.datetime_submitted is not None
        ):
            context["revoke_deadline"] = (
                self.foia.composer.datetime_submitted
                + timedelta(seconds=COMPOSER_EDIT_DELAY)
            )
            context["can_revoke"] = (
                context["user_can_edit"] and self.foia.composer.revokable()
            )

    def _get_agency_context_data(self, context):
        """Get context data for agency users"""

        context["can_agency_reply"] = (
            self.foia.has_perm(self.request.user, "agency_reply") or self.valid_passcode
        )
        context["is_agency_user"] = (
            self.request.user.is_authenticated
            and self.request.user.profile.is_agency_user
        ) or (
            not self.request.user.is_authenticated
            and (self.valid_passcode or "agency" in self.request.GET)
        )
        context["agency_status_choices"] = AGENCY_STATUS
        context["unauthenticated_agency"] = (
            not self.request.user.is_authenticated
            and "agency" in self.request.GET
            and not self.valid_passcode
        )

    def get(self, request, *args, **kwargs):
        """Mark any unread notifications for this object as read."""
        user = request.user
        if user.is_authenticated:
            notifications = (
                Notification.objects.for_user(user).for_object(self.foia).get_unread()
            )
            for notification in notifications:
                notification.mark_read()
        if self.foia.has_perm(request.user, "zip_download") and request.GET.get(
            "zip_download"
        ):
            return self._get_zip_download()

        if self.foia.sidebar_html:
            messages.info(request, self.foia.sidebar_html)

        return super(Detail, self).get(request, *args, **kwargs)

    def post(self, request):
        """Handle form submissions"""
        action = getattr(detail_actions, request.POST.get("action", ""), None)
        if action is None:
            messages.error(request, "Something went wrong")
            return redirect(self.foia)
        return action(request, self.foia)

    def _get_zip_download(self):
        """Get a zip file of the entire request"""
        if self.foia.has_perm(self.request.user, "zip_download"):
            zip_request.delay(self.foia.pk, self.request.user.pk)
            messages.info(
                self.request,
                "Your zip archive is being processed.  It will be emailed to you when "
                "it is ready.",
            )
        return redirect(self.foia.get_absolute_url() + "#")


class MultiDetail(DetailView):
    """Detail view for multi requests"""

    model = FOIAMultiRequest
    query_pk_and_slug = True

    def dispatch(self, request, *args, **kwargs):
        """Redirect to corresponding composer"""
        multi = self.get_object()
        return redirect(multi.composer)


class ComposerDetail(DetailView):
    """Detail view for multi requests"""

    model = FOIAComposer
    context_object_name = "composer"
    query_pk_and_slug = True
    pk_url_kwarg = "idx"
    template_name = "foia/foiacomposer_detail.html"

    def get(self, request, *args, **kwargs):
        """If composer is a draft, then redirect to drafting interface"""
        # pylint: disable=attribute-defined-outside-init
        composer = self.get_object()
        can_edit = composer.has_perm(self.request.user, "change")
        if composer.status == "started" and can_edit:
            return redirect("foia-draft", idx=composer.pk)
        if composer.status == "started" and not can_edit:
            raise Http404
        self.foias = composer.foias.get_viewable(
            self.request.user
        ).select_related_view()
        if not can_edit and not self.foias:
            raise Http404
        if len(self.foias) == 1:
            return redirect(self.foias[0])
        return super(ComposerDetail, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(ComposerDetail, self).get_context_data(**kwargs)
        composer = context["composer"]
        context["foias"] = self.foias
        context["sidebar_admin_url"] = reverse(
            "admin:foia_foiacomposer_change", args=(composer.pk,)
        )
        context["processing"] = composer.status == "submitted" and (
            composer.foias.count() != composer.agencies.count()
        )
        if composer.status == "submitted" and composer.datetime_submitted is not None:
            context["edit_deadline"] = composer.datetime_submitted + timedelta(
                seconds=COMPOSER_EDIT_DELAY
            )
            context["can_edit"] = (
                timezone.now() < context["edit_deadline"]
                and composer.delayed_id
                and composer.has_perm(self.request.user, "change")
            )
        return context

    def post(self, request, *args, **kwargs):
        """Handle send it now action

        This uses celery's inspection tools to pull out the arguments for the
        composer_delayed_submit task, revoke it, and then call it immediately with the
        correct args
        """
        # pylint: disable=unused-argument
        composer = self.get_object()
        if (
            request.POST.get("action") == "send-now"
            and request.user.is_staff
            and composer.revokable()
        ):
            scheduled = current_app.control.inspect().scheduled()
            if scheduled is None:
                # if no tasks are scheduled, something has gone wrong
                messages.error(request, "This request could not be sent")
                return redirect(composer)
            for tasks in scheduled.values():
                for task in tasks:
                    if task["request"]["id"] == composer.delayed_id:
                        current_app.control.revoke(composer.delayed_id)
                        composer_delayed_submit.delay(*task["request"]["args"])
                        return redirect(composer)
            # if we don't return from the for loop, we could not find the task
            # something has gone wrong
            messages.error(request, "This request could not be sent")

        return redirect(composer)
