"""
Detail view for a FOIA request
"""

# pylint: disable=too-many-lines

# Django
from celery import current_app
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

# Standard Library
import itertools
import json
import logging
import sys
from datetime import timedelta
from heapq import merge

# Third Party
import requests
from constance import config

# MuckRock
from muckrock.accounts.models import Notification
from muckrock.accounts.utils import mixpanel_event
from muckrock.agency.forms import AgencyForm
from muckrock.communication.models import (
    Check,
    EmailCommunication,
    FaxCommunication,
    WebCommunication,
)
from muckrock.core.utils import new_action
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.constants import COMPOSER_EDIT_DELAY
from muckrock.foia.exceptions import FoiaFormError
from muckrock.foia.forms import (
    ContactInfoForm,
    FOIAAccessForm,
    FOIAAdminFixForm,
    FOIAAgencyReplyForm,
    FOIAContactUserForm,
    FOIAEmbargoForm,
    FOIAEstimatedCompletionDateForm,
    FOIAFlagForm,
    FOIANoteForm,
    FOIASoftDeleteForm,
    RequestFeeForm,
    ResendForm,
    TrackingNumberForm,
)
from muckrock.foia.models import (
    END_STATUS,
    STATUS,
    FOIACommunication,
    FOIAComposer,
    FOIAFile,
    FOIAMultiRequest,
    FOIARequest,
)
from muckrock.foia.tasks import (
    composer_delayed_submit,
    import_doccloud_file,
    zip_request,
)
from muckrock.jurisdiction.forms import AppealForm
from muckrock.jurisdiction.models import Appeal
from muckrock.message.email import TemplateEmail
from muckrock.portal.forms import PortalForm
from muckrock.project.forms import ProjectManagerForm
from muckrock.tags.models import Tag
from muckrock.task.models import FlaggedTask, ResponseTask, StatusChangeTask, Task

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
        self._obj = None
        self.agency_reply_form = FOIAAgencyReplyForm()
        self.admin_fix_form = None
        self.resend_forms = None
        self.fee_form = None
        super(Detail, self).__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        """Handle forms"""
        foia = self.get_object()
        self.admin_fix_form = FOIAAdminFixForm(
            prefix="admin_fix",
            request=self.request,
            foia=self.get_object(),
            initial={
                "subject": foia.default_subject(),
                "other_emails": foia.cc_emails.all(),
            },
        )
        self.resend_forms = {
            c.pk: ResendForm(prefix=str(c.pk)) for c in foia.communications.all()
        }
        self.fee_form = RequestFeeForm(
            user=self.request.user, initial={"amount": foia.get_stripe_amount()}
        )
        if request.POST:
            try:
                return self.post(request)
            except FoiaFormError:
                # if their is a form error, continue onto the GET path
                # and show the invalid form with errors displayed
                return self.get(request, *args, **kwargs)

        return super(Detail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        # pylint: disable=unused-argument
        # pylint: disable=unsubscriptable-object
        # this is called twice in dispatch, so cache to not actually run twice
        if self._obj:
            return self._obj

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
        valid_access_key = self.request.GET.get("key") == foia.access_key
        has_perm = foia.has_perm(self.request.user, "view")
        if not has_perm and not valid_access_key:
            raise Http404()
        self._obj = foia
        return foia

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        # pylint: disable=too-many-statements, too-many-locals
        context = super(Detail, self).get_context_data(**kwargs)
        foia = context["foia"]
        user = self.request.user
        user_can_edit = foia.has_perm(self.request.user, "change")
        user_can_embargo = foia.has_perm(self.request.user, "embargo")
        is_past_due = foia.date_due < timezone.now().date() if foia.date_due else False
        context["all_tags"] = Tag.objects.all()
        context["past_due"] = is_past_due
        context["user_can_edit"] = user_can_edit
        context["user_can_pay"] = (
            foia.has_perm(self.request.user, "pay") and foia.status == "payment"
        )
        context["embargo"] = {
            "show": user_can_embargo or foia.embargo,
            "edit": user_can_embargo,
            "add": user_can_embargo,
            "remove": user_can_edit and foia.embargo,
        }
        context["embargo_form"] = FOIAEmbargoForm(
            initial={
                "permanent_embargo": foia.permanent_embargo,
                "date_embargo": foia.date_embargo,
            }
        )
        context["note_form"] = FOIANoteForm()
        context["access_form"] = FOIAAccessForm()
        context["crowdfund_form"] = CrowdfundForm(
            initial={
                "name": "Crowdfund Request: %s" % str(foia),
                "description": "Help cover the request fees needed to free these docs!",
                "payment_required": foia.get_stripe_amount(),
                "date_due": timezone.now() + timedelta(30),
                "foia": foia,
            }
        )
        context["fee_form"] = self.fee_form

        context["embargo_needs_date"] = foia.status in END_STATUS
        context["user_actions"] = foia.user_actions(user)
        context["status_choices"] = [(k, v) for (k, v) in STATUS if k != "submitted"]
        context["show_estimated_date"] = foia.status not in [
            "submitted",
            "ack",
            "done",
            "rejected",
        ]
        context["change_estimated_date"] = FOIAEstimatedCompletionDateForm(
            instance=foia
        )
        context["tracking_id_form"] = TrackingNumberForm()
        context["portal_form"] = PortalForm(foia=foia)
        context["contact_info_form"] = ContactInfoForm(foia=foia, prefix="followup")
        context["appeal_contact_info_form"] = ContactInfoForm(
            foia=foia, appeal=True, prefix="appeal"
        )

        if user_can_edit or user.is_staff:
            all_tasks = Task.objects.filter_by_foia(foia, user)
            open_tasks = [task for task in all_tasks if not task.resolved]
            context["task_count"] = len(all_tasks)
            context["open_task_count"] = len(open_tasks)
            context["open_tasks"] = open_tasks
            context["asignees"] = (
                User.objects.filter(is_staff=True)
                .select_related("profile")
                .order_by("profile__full_name")
            )

        context["sidebar_admin_url"] = reverse(
            "admin:foia_foiarequest_change", args=(foia.pk,)
        )
        context["is_thankable"] = foia.has_perm(self.request.user, "thank")
        context["files"] = foia.get_files().select_related("comm__foia")[:50]
        if self.request.user.is_authenticated:
            context["foia_cache_timeout"] = 0
        else:
            context["foia_cache_timeout"] = settings.DEFAULT_CACHE_TIMEOUT
        context["settings"] = settings
        context["agency_status_choices"] = AGENCY_STATUS
        context["agency_reply_form"] = self.agency_reply_form
        context["admin_fix_form"] = self.admin_fix_form
        context["resend_forms"] = self.resend_forms
        context["cc_emails"] = json.dumps([str(e) for e in foia.cc_emails.all()])
        notes = [
            (n.datetime, "note", n) for n in foia.notes.select_related("author").all()
        ]
        checks = [
            (c.created_datetime, "check", c)
            for c in Check.objects.filter(communication__foia=foia)
            .select_related("user__profile")
            .prefetch_related("communication__mails__events")
        ]
        context["notes"] = [(t, v) for _, t, v in merge(notes, checks)]
        if (
            foia.composer.status == "submitted"
            and foia.composer.datetime_submitted is not None
        ):
            context["revoke_deadline"] = foia.composer.datetime_submitted + timedelta(
                seconds=COMPOSER_EDIT_DELAY
            )
            context["can_revoke"] = user_can_edit and foia.composer.revokable()
        if foia.sidebar_html:
            messages.info(self.request, foia.sidebar_html)
        if foia.noindex:
            context["meta_noindex"] = True
        context["enable_followup"] = config.ENABLE_FOLLOWUP
        context["disabled_followup_message"] = config.DISABLED_FOLLOWUP_MESSAGE
        return context

    def get(self, request, *args, **kwargs):
        """Mark any unread notifications for this object as read."""
        user = request.user
        foia = self.get_object()
        if user.is_authenticated:
            notifications = (
                Notification.objects.for_user(user).for_object(foia).get_unread()
            )
            for notification in notifications:
                notification.mark_read()
        if foia.has_perm(request.user, "zip_download") and request.GET.get(
            "zip_download"
        ):
            return self._get_zip_download()
        return super(Detail, self).get(request, *args, **kwargs)

    def post(self, request):
        """Handle form submissions"""
        foia = self.get_object()
        actions = {
            "status": self._status,
            "tags": self._tags,
            "projects": self._projects,
            "follow_up": self._follow_up,
            "thanks": self._thank,
            "add_note": self._add_note,
            "flag": self._flag,
            "delete": self._delete,
            "contact_user": self._contact_user,
            "appeal": self._appeal,
            "date_estimate": self._update_estimate,
            "status_comm": self._change_comm_status,
            "move_comm": self._move_comm,
            "delete_comm": self._delete_comm,
            "resend_comm": self._resend_comm,
            "generate_key": self._generate_key,
            "grant_access": self._grant_access,
            "revoke_access": self._revoke_access,
            "demote": self._demote_editor,
            "promote": self._promote_viewer,
            "update_new_agency": self._update_new_agency,
            "agency_reply": self._agency_reply,
            "staff_pay": self._staff_pay,
            "pay_fee": self._pay_fee,
            "tracking_id": self._tracking_id,
            "portal": self._portal,
            "import_dc_file": self._import_dc_file,
            "delete_file": self._delete_file,
        }
        try:
            return actions[request.POST["action"]](request, foia)
        except KeyError:  # if submitting form from web page improperly
            return redirect(foia)

    def _tags(self, request, foia):
        """Handle updating tags"""
        if foia.has_perm(request.user, "change"):
            foia.update_tags(request.POST.getlist("tags"))
        return redirect(foia.get_absolute_url() + "#")

    def _projects(self, request, foia):
        """Handle updating projects"""
        form = ProjectManagerForm(request.POST, user=request.user)
        has_perm = foia.has_perm(request.user, "change")
        if has_perm and form.is_valid():
            projects = form.cleaned_data["projects"]
            for proj in itertools.chain(foia.projects.all(), projects):
                # clear cache for old and new projects
                proj.clear_cache()
            foia.projects.set(projects)
        return redirect(foia.get_absolute_url() + "#")

    def _status(self, request, foia):
        """Handle updating status"""
        allowed_statuses = [s for s, _ in STATUS if s != "submitted"]
        status = request.POST.get("status")
        old_status = foia.get_status_display()
        has_perm = foia.has_perm(request.user, "change")
        user_editable = has_perm and status in allowed_statuses
        staff_editable = request.user.is_staff and status in allowed_statuses
        if foia.status != "submitted" and (user_editable or staff_editable):
            foia.status = status
            foia.save(comment="status updated")
            if staff_editable:
                kwargs = {
                    "resolved": True,
                    "resolved_by": request.user,
                    "date_done": timezone.now(),
                }
            else:
                kwargs = {}
            StatusChangeTask.objects.create(
                user=request.user, old_status=old_status, foia=foia, **kwargs
            )
            response_tasks = ResponseTask.objects.filter(
                resolved=False, communication__foia=foia
            )
            for task in response_tasks:
                task.resolve(request.user)
        return redirect(foia.get_absolute_url() + "#")

    def _add_note(self, request, foia):
        """Adds a note to the request"""
        note_form = FOIANoteForm(request.POST)
        has_perm = foia.has_perm(request.user, "change")
        if has_perm and note_form.is_valid():
            foia_note = note_form.save(commit=False)
            foia_note.foia = foia
            foia_note.author = request.user
            foia_note.datetime = timezone.now()
            foia_note.save()
            logger.info(
                "%s added %s to %s", foia_note.author, foia_note, foia_note.foia
            )
            messages.success(request, "Your note is attached to the request.")
        return redirect(foia.get_absolute_url() + "#")

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        form = FOIAFlagForm(request.POST)
        has_perm = foia.has_perm(request.user, "flag")
        if has_perm and form.is_valid():
            FlaggedTask.objects.create(
                user=request.user,
                foia=foia,
                text=form.cleaned_data["text"],
                category=form.cleaned_data["category"],
            )
            messages.success(request, "Problem succesfully reported")
            new_action(request.user, "flagged", target=foia)
        return redirect(foia.get_absolute_url() + "#")

    def _delete(self, request, foia):
        """Allow staff to soft delete requests"""
        form = FOIASoftDeleteForm(request.POST, foia=foia)
        has_perm = request.user.has_perm("foia.delete_foiarequest")
        if has_perm and form.is_valid():
            foia.soft_delete(
                request.user,
                # final message is not used when foia is in an end state
                form.cleaned_data.get("final_message", ""),
                form.cleaned_data["note"],
            )
            messages.success(request, "Request succesfully deleted")
        return redirect(foia.get_absolute_url() + "#")

    def _contact_user(self, request, foia):
        """Allow an admin to message the foia's owner"""
        form = FOIAContactUserForm(request.POST)
        if request.user.is_staff and form.is_valid() and form.cleaned_data["text"]:
            context = {
                "text": form.cleaned_data["text"],
                "foia_url": foia.user.profile.wrap_url(foia.get_absolute_url()),
                "foia_title": foia.title,
            }
            email = TemplateEmail(
                user=foia.user,
                extra_context=context,
                text_template="message/notification/contact_user.txt",
                html_template="message/notification/contact_user.html",
                subject="Message from MuckRock",
            )
            email.send(fail_silently=False)
            messages.success(request, "Email sent to %s" % foia.user.email)
        return redirect(foia.get_absolute_url() + "#")

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        if request.user.is_anonymous:
            messages.error(request, "You must be logged in to follow up")
            return redirect(foia.get_absolute_url() + "#")
        if foia.attachments_over_size_limit(request.user):
            messages.error(request, "Total attachment size must be less than 20MB")
            return redirect(foia.get_absolute_url() + "#")
        if request.user.is_staff:
            return self._admin_follow_up(request, foia)
        else:
            return self._user_follow_up(request, foia)

    def _admin_follow_up(self, request, foia):
        """Handle follow ups for admins"""
        form = FOIAAdminFixForm(
            request.POST, prefix="admin_fix", request=request, foia=foia
        )
        if form.is_valid():
            foia.update_address(
                form.cleaned_data["via"],
                email=form.cleaned_data["email"],
                other_emails=form.cleaned_data["other_emails"],
                fax=form.cleaned_data["fax"],
            )
            snail = form.cleaned_data["via"] == "snail"
            foia.create_out_communication(
                from_user=form.cleaned_data["from_user"],
                text=form.cleaned_data["comm"],
                user=request.user,
                snail=snail,
                subject=form.cleaned_data["subject"],
            )
            messages.success(request, "Your follow up has been sent.")
            new_action(request.user, "followed up on", target=foia)
            return redirect(foia.get_absolute_url() + "#")
        else:
            self.admin_fix_form = form
            raise FoiaFormError

    def _user_follow_up(self, request, foia):
        """Handle follow ups for non-admins"""
        has_perm = foia.has_perm(request.user, "followup")
        contact_info_form = ContactInfoForm(request.POST, foia=foia, prefix="followup")
        has_contact_perm = request.user.has_perm("foia.set_info_foiarequest")
        contact_valid = contact_info_form.is_valid()
        use_contact_info = has_contact_perm and contact_info_form.cleaned_data.get(
            "use_contact_information"
        )
        comm_sent = self._new_comm(
            request,
            foia,
            has_perm and (not use_contact_info or contact_valid),
            "Your follow up has been sent.",
            contact_info=contact_info_form.cleaned_data if use_contact_info else None,
        )
        if use_contact_info:
            foia.add_contact_info_note(request.user, contact_info_form.cleaned_data)
        if comm_sent:
            new_action(request.user, "followed up on", target=foia)
            mixpanel_event(
                request,
                "Follow Up",
                foia.mixpanel_data({"Use Contact Info": use_contact_info}),
            )
        return redirect(foia.get_absolute_url() + "#")

    def _thank(self, request, foia):
        """Handle submitting a thank you follow up"""
        success_msg = "Your thank you has been sent."
        has_perm = foia.has_perm(request.user, "thank")
        comm_sent = self._new_comm(request, foia, has_perm, success_msg, thanks=True)
        if comm_sent:
            new_action(request.user, verb="thanked", target=foia.agency)
        return redirect(foia.get_absolute_url() + "#")

    def _new_comm(self, request, foia, test, success_msg, **kwargs):
        """Helper function for sending a new comm"""
        # pylint: disable=too-many-arguments
        text = request.POST.get("text")
        comm_sent = False
        if text and test:
            foia.create_out_communication(
                from_user=request.user, text=text, user=request.user, **kwargs
            )
            messages.success(request, success_msg)
            comm_sent = True
        return comm_sent

    def _appeal(self, request, foia):
        """Handle submitting an appeal, then create an Appeal from the returned
        communication.
        """
        form = AppealForm(request.POST)
        has_perm = foia.has_perm(request.user, "appeal")
        contact_info_form = ContactInfoForm(
            request.POST, foia=foia, prefix="appeal", appeal=True
        )
        has_contact_perm = request.user.has_perm("foia.set_info_foiarequest")
        contact_valid = contact_info_form.is_valid()
        use_contact_info = has_contact_perm and contact_info_form.cleaned_data.get(
            "use_contact_information"
        )
        if not has_perm:
            messages.error(request, "You do not have permission to submit an appeal.")
            return redirect(foia.get_absolute_url() + "#")
        if not form.is_valid():
            messages.error(request, "You did not submit an appeal.")
            return redirect(foia.get_absolute_url() + "#")
        if foia.attachments_over_size_limit(request.user):
            messages.error(request, "Total attachment size must be less than 20MB")
            return redirect(foia.get_absolute_url() + "#")
        if use_contact_info and not contact_valid:
            messages.error(request, "Invalid contact information")
            return redirect(foia.get_absolute_url() + "#")
        communication = foia.appeal(
            form.cleaned_data["text"],
            request.user,
            contact_info=contact_info_form.cleaned_data if use_contact_info else None,
        )
        base_language = form.cleaned_data["base_language"]
        appeal = Appeal.objects.create(communication=communication)
        appeal.base_language.set(base_language)
        new_action(request.user, "appealed", target=foia)
        messages.success(request, "Your appeal has been sent.")
        if use_contact_info:
            foia.add_contact_info_note(request.user, contact_info_form.cleaned_data)
        return redirect(foia.get_absolute_url() + "#")

    def _update_estimate(self, request, foia):
        """Change the estimated completion date"""
        form = FOIAEstimatedCompletionDateForm(request.POST, instance=foia)
        if foia.has_perm(request.user, "change"):
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Successfully changed the estimated completion date."
                )
            else:
                messages.error(request, "Invalid date provided.")
        else:
            messages.error(request, "You cannot do that, stop it.")
        return redirect(foia.get_absolute_url() + "#")

    def _tracking_id(self, request, foia):
        """Add a new tracking ID"""
        form = TrackingNumberForm(request.POST)
        if request.user.is_staff:
            if form.is_valid():
                tracking_id = form.save(commit=False)
                tracking_id.foia = foia
                tracking_id.save()
                messages.success(request, "Successfully added a tracking number")
            else:
                messages.error(
                    request, "Please fill out the tracking number and reason"
                )
        else:
            messages.error(request, "You do not have permission to do that")
        return redirect(foia.get_absolute_url() + "#")

    def _portal(self, request, foia):
        """Add a new or existing portal"""
        form = PortalForm(request.POST, foia=foia)
        if request.user.is_staff:
            if form.is_valid():
                form.save()
                messages.success(request, "Successfully added a portal")
            else:
                messages.error(
                    request, "Choose a portal or supply information for a new one"
                )
        else:
            messages.error(request, "You do not have permission to do that")
        return redirect(foia.get_absolute_url() + "#")

    def _update_new_agency(self, request, foia):
        """Update the new agency"""
        form = AgencyForm(
            request.POST, instance=foia.agency, prefix=request.POST.get("task", "")
        )
        if foia.has_perm(request.user, "change"):
            if form.is_valid():
                form.save()
                messages.success(request, "Agency info saved. Thanks for your help!")
            else:
                messages.error(request, "The data was invalid! Try again.")
        else:
            messages.error(request, "You cannot do that, stop it.")
        return redirect(foia.get_absolute_url() + "#")

    def _generate_key(self, request, foia):
        """Generate and return an access key, with support for AJAX."""
        if not foia.has_perm(request.user, "change"):
            if request.is_ajax():
                return PermissionDenied
            else:
                return redirect(foia.get_absolute_url() + "#")
        else:
            key = foia.generate_access_key()
            if request.is_ajax():
                return JsonResponse({"key": key})
            else:
                messages.success(request, "New private link created.")
                return redirect(foia.get_absolute_url() + "#")

    def _grant_access(self, request, foia):
        """Grant editor access to the specified users."""
        form = FOIAAccessForm(request.POST)
        has_perm = foia.has_perm(request.user, "change")
        if not has_perm or not form.is_valid():
            return redirect(foia.get_absolute_url() + "#")
        access = form.cleaned_data["access"]
        users = form.cleaned_data["users"]
        if access == "edit" and users:
            for user in users:
                foia.add_editor(user)
        if access == "view" and users:
            for user in users:
                foia.add_viewer(user)
        if len(users) > 1:
            success_msg = "%d people can now %s this request." % (len(users), access)
        else:
            success_msg = "%s can now %s this request." % (
                users[0].profile.full_name,
                access,
            )
        messages.success(request, success_msg)
        return redirect(foia.get_absolute_url() + "#")

    def _revoke_access(self, request, foia):
        """Revoke access from a user."""
        user_pk = request.POST.get("user")
        user = User.objects.get(pk=user_pk)
        has_perm = foia.has_perm(request.user, "change")
        if has_perm and user:
            if foia.has_editor(user):
                foia.remove_editor(user)
            elif foia.has_viewer(user):
                foia.remove_viewer(user)
            messages.success(
                request,
                "%s no longer has access to this request." % user.profile.full_name,
            )
        return redirect(foia.get_absolute_url() + "#")

    def _demote_editor(self, request, foia):
        """Demote user from editor access to viewer access"""
        user_pk = request.POST.get("user")
        user = User.objects.get(pk=user_pk)
        has_perm = foia.has_perm(request.user, "change")
        if has_perm and user:
            foia.demote_editor(user)
            messages.success(
                request, "%s can now only view this request." % user.profile.full_name
            )
        return redirect(foia.get_absolute_url() + "#")

    def _promote_viewer(self, request, foia):
        """Promote user from viewer access to editor access"""
        user_pk = request.POST.get("user")
        user = User.objects.get(pk=user_pk)
        has_perm = foia.has_perm(request.user, "change")
        if has_perm and user:
            foia.promote_viewer(user)
            messages.success(
                request, "%s can now edit this request." % user.profile.full_name
            )
        return redirect(foia.get_absolute_url() + "#")

    def _agency_reply(self, request, foia):
        """Agency reply directly through the site"""
        has_perm = foia.has_perm(self.request.user, "agency_reply")
        if has_perm:
            form = FOIAAgencyReplyForm(request.POST)
            if form.is_valid():
                comm = FOIACommunication.objects.create(
                    foia=foia,
                    from_user=request.user,
                    to_user=foia.user,
                    response=True,
                    datetime=timezone.now(),
                    communication=form.cleaned_data["reply"],
                    status=form.cleaned_data["status"],
                )
                WebCommunication.objects.create(
                    communication=comm, sent_datetime=timezone.now()
                )
                foia.date_estimate = form.cleaned_data["date_estimate"]
                foia.add_tracking_id(form.cleaned_data["tracking_id"])
                foia.status = form.cleaned_data["status"]
                if foia.status == "payment":
                    foia.price = form.cleaned_data["price"] / 100.0
                foia.save()
                foia.process_attachments(request.user)
                comm.create_agency_notifications()
                FlaggedTask.objects.create(
                    user=self.request.user,
                    foia=foia,
                    text="An agency used its login to update this request",
                )
                messages.success(request, "Reply succesfully posted")
            else:
                self.agency_reply_form = form
                raise FoiaFormError

        return redirect(foia.get_absolute_url() + "#")

    def _staff_pay(self, request, foia):
        """Staff pays for a request without using stripe"""
        has_perm = self.request.user.is_staff
        if has_perm:
            amount = request.POST.get("amount")
            try:
                amount = int(amount)
            except (ValueError, TypeError):
                messages.error(request, "Not a valid amount")
            else:
                foia.pay(request.user, amount / 100.0)
        return redirect(foia.get_absolute_url() + "#")

    def _pay_fee(self, request, foia):
        """A user pays the fee for a request"""
        form = RequestFeeForm(request.POST, user=self.request.user)
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Must be logged in to pay")
            return redirect(foia.get_absolute_url() + "#")
        if form.is_valid():
            try:
                form.cleaned_data["organization"].pay(
                    amount=int(form.cleaned_data["amount"] * 1.05),
                    fee_amount=5,
                    description="Pay ${:.2f} fee for request #{}".format(
                        form.cleaned_data["amount"] / 100.0, foia.pk
                    ),
                    token=form.cleaned_data["stripe_token"],
                    save_card=form.cleaned_data["save_card"],
                )
            except requests.exceptions.RequestException as exc:
                logger.warning("Payment error: %s", exc, exc_info=sys.exc_info())
                if exc.response.status_code // 100 == 4:
                    messages.error(
                        self.request,
                        "Payment Error: {}".format(
                            "\n".join(
                                "{}: {}".format(k, v)
                                for k, v in exc.response.json().items()
                            )
                        ),
                    )
                else:
                    messages.error(self.request, "Payment Error")
                return redirect(foia.get_absolute_url() + "#")
            else:
                messages.success(
                    self.request,
                    "Your payment was successful. "
                    "We will get this to the agency right away!",
                )
                amount = form.cleaned_data["amount"] / 100.0
                foia.pay(self.request.user, amount)
                mixpanel_event(
                    request,
                    "Request Fee Paid",
                    foia.mixpanel_data({"Price": amount}),
                    charge=amount,
                )
                return redirect(foia.get_absolute_url() + "#")
        else:
            self.fee_form = form
            raise FoiaFormError

    def _resend_comm(self, request, foia):
        """Resend a communication"""
        if request.user.is_staff:
            form = ResendForm(
                request.POST, prefix=request.POST.get("communication", "")
            )
            if form.is_valid():
                foia.update_address(
                    form.cleaned_data["via"],
                    email=form.cleaned_data["email"],
                    fax=form.cleaned_data["fax"],
                )
                snail = form.cleaned_data["via"] == "snail"
                foia.submit(snail=snail, comm=form.cleaned_data["communication"])
                messages.success(request, "The communication was resent")
            else:
                comm = form.cleaned_data.get("communication")
                if comm:
                    self.resend_forms[comm.id] = form
                raise FoiaFormError
        return redirect(foia.get_absolute_url() + "#")

    def _move_comm(self, request, foia):
        """Admin moves a communication to a different FOIA"""
        if request.user.is_staff:
            try:
                comm_pk = request.POST["comm_pk"]
                comm = FOIACommunication.objects.get(pk=comm_pk)
                new_foia_pks = request.POST["new_foia_pks"].split(",")
                comm.move(new_foia_pks, request.user)
                messages.success(request, "Communication moved successfully")
            except (KeyError, FOIACommunication.DoesNotExist):
                messages.error(request, "The communication does not exist.")
            except ValueError:
                messages.error(request, "No move destination provided.")
        return redirect(foia.get_absolute_url() + "#")

    def _delete_comm(self, request, foia):
        """Admin deletes a communication"""
        if request.user.is_staff:
            try:
                comm = FOIACommunication.objects.get(pk=request.POST["comm_pk"])
                files = comm.files.all()
                for file_ in files:
                    file_.delete()
                comm.delete()
                messages.success(request, "The communication was deleted.")
            except (KeyError, FOIACommunication.DoesNotExist):
                messages.error(request, "The communication does not exist.")
        return redirect(foia.get_absolute_url() + "#")

    def _change_comm_status(self, request, foia):
        """Change the status of a communication"""
        if request.user.is_staff:
            try:
                comm = FOIACommunication.objects.get(pk=request.POST["comm_pk"])
                status = request.POST.get("status", "")
                if status in [s for s, _ in STATUS]:
                    comm.status = status
                    comm.save()
            except (KeyError, FOIACommunication.DoesNotExist):
                messages.error(request, "The communication does not exist.")
        return redirect(foia.get_absolute_url() + "#")

    def _import_dc_file(self, request, foia):
        """Import a file from DocumentCloud"""
        if request.user.is_staff:
            file_pk = request.POST.get("file_pk")
            import_doccloud_file.delay(file_pk)
            messages.success(
                request, "The file will be imported from DocumentCloud soon"
            )
        return redirect(foia.get_absolute_url() + "#")

    def _delete_file(self, request, foia):
        """Import a file from DocumentCloud"""
        if request.user.is_staff:
            file_pk = request.POST.get("file_pk")
            FOIAFile.objects.filter(pk=file_pk).delete()
            messages.success(request, "File succesfully deleted")
        return redirect(foia.get_absolute_url() + "#")

    def _get_zip_download(self):
        """Get a zip file of the entire request"""
        foia = self.get_object()
        if foia.has_perm(self.request.user, "zip_download"):
            zip_request.delay(foia.pk, self.request.user.pk)
            messages.info(
                self.request,
                "Your zip archive is being processed.  It will be emailed to you when "
                "it is ready.",
            )
        return redirect(foia.get_absolute_url() + "#")


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
