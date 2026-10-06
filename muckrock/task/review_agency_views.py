# -*- coding: utf-8 -*-
"""
The review agency detail view

One URL for one agency's whole channel roster.  Lives in its own module rather
than in views.py: this is the surface the channel work is built around, and
views.py is already at the size limit.
"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.generic import DetailView

# MuckRock
from muckrock.agency.models import Agency
from muckrock.communication.models import EmailAddress, FaxError
from muckrock.core.views import class_view_decorator
from muckrock.foia.models import FOIARequest
from muckrock.task.channels import agency_channels, agency_rollup, serialize_channels
from muckrock.task.forms import ChannelRepairForm
from muckrock.task.models import ReviewAgencyTask


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class ReviewAgencyDetailView(DetailView):
    """Triage and repair all of one agency's communication channels

    A real URL rather than an inline AJAX panel: shareable, back button works,
    and heavy work does not push the queue off screen.  Today's inline panel is
    an artifact of the original implementation, not a requirement.

    Sized for 1-2 channels (the 81.7% majority and p90), comfortable to 5
    (p99), and still usable at 23 (the FBI).
    """

    model = Agency
    context_object_name = "agency"
    template_name = "task/review_agency_detail.html"

    def get_queryset(self):
        """The agency plus what the header needs"""
        return Agency.objects.select_related("jurisdiction", "portal")

    def get_context_data(self, **kwargs):
        """The channel roster, the scorecard, and the Svelte payload"""
        context = super().get_context_data(**kwargs)
        agency = self.object

        channels = agency_channels(agency)
        context["channels"] = channels
        context.update(agency_rollup(agency, channels=channels))

        # Behind a disclosure at the top of the page -- close at hand for
        # finding or asking after new contact info, without crowding out what
        # is actually broken.
        # Not Agency.email, which skips broken addresses -- and a broken
        # primary is usually why the agency is here.
        primary_emails = list(
            agency.agencyemail_set.filter(
                request_type="primary", email_type="to"
            ).select_related("email")
        )
        # Every roster address is already a channel, with its error decoded
        channels_by_address = {channel.address.pk: channel for channel in channels}
        for link in primary_emails:
            channel = channels_by_address.get(link.email_id)
            link.error_summary = _error_summary(
                channel and channel.last_error_message,
                channel and channel.last_error,
            )
        context["primary_emails"] = primary_emails

        agency_phones = list(agency.agencyphone_set.select_related("phone"))
        fax_errors = _latest_fax_errors([link.phone_id for link in agency_phones])
        for link in agency_phones:
            error = fax_errors.get(link.phone_id)
            link.error_summary = _error_summary(
                error and (error.error_code or error.error_type),
                error and error.datetime,
            )
        context["faxes"] = [link for link in agency_phones if link.phone.type == "fax"]
        context["phones"] = [
            link for link in agency_phones if link.phone.type == "phone"
        ]
        # Only the addresses requests go to are worth listing; the rest are
        # counted, with the full roster a click away in the admin
        agency_addresses = list(agency.agencyaddress_set.select_related("address"))
        context["addresses"] = [
            link
            for link in agency_addresses
            if link.request_type in ("primary", "appeal")
        ]
        context["other_address_count"] = len(agency_addresses) - len(
            context["addresses"]
        )

        context["open_tasks"] = ReviewAgencyTask.objects.filter(
            agency=agency, resolved=False
        ).select_related("email")
        context["repair_form"] = kwargs.get("repair_form") or ChannelRepairForm()
        context["channels_json"] = serialize_channels(agency, channels)
        return context

    def post(self, request, *args, **kwargs):
        """Apply a repair to one or several of this agency's channels"""
        self.object = self.get_object()
        form = ChannelRepairForm(request.POST)
        if not form.is_valid():
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else None
                for error in errors:
                    messages.error(request, f"{label}: {error}" if label else error)
            context = self.get_context_data(object=self.object, repair_form=form)
            return self.render_to_response(context)

        channels = list(
            EmailAddress.objects.filter(pk__in=form.cleaned_data["channel_pks"])
        )
        foias = list(
            FOIARequest.objects.filter(
                pk__in=form.cleaned_data["foia_pks"]
            ).select_related("email")
        )
        # Read before the repair repoints them, and from the selection rather
        # than the tasks matched: a channel covered by the agency level task
        # has no task of its own
        old_emails = sorted(
            {channel.email for channel in channels}
            or {foia.email.email for foia in foias if foia.email}
        )

        tasks = ReviewAgencyTask.repair_channels(
            agency=self.object,
            user=request.user,
            new_email=form.cleaned_data["new_email"],
            channels=channels,
            foias=foias,
            update_info=form.cleaned_data["update_agency_info"],
            snail=form.cleaned_data["snail_mail"],
            resolve=form.cleaned_data["resolve"],
            reply=form.cleaned_data["reply"],
        )
        messages.success(
            request,
            _repair_message(self.object, form.cleaned_data, foias, old_emails, tasks),
        )
        # Back to the queue, scoped to this agency, where its new blocked total
        # shows whether anything is left before the task can be resolved.
        # Once every task is resolved that view would be empty, so the whole
        # queue it is.
        queue_url = reverse("review-agency-task-list")
        if ReviewAgencyTask.objects.filter(agency=self.object, resolved=False).exists():
            queue_url += "?agency=%d" % self.object.pk
        return redirect(queue_url)


def _plural(count, word):
    """'1 request', '2 requests'"""
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def _repair_message(agency, data, foias, old_emails, tasks):
    """What a repair did, and what it left for the staffer to do

    Each part of the submission gets a clause, including the ones that did
    nothing -- a resolve with no replacement address is easy to submit by
    accident now resolve starts checked.  A task the repair touched but left
    open is named, since it no longer stands out in the queue on its own.
    """
    parts = []
    if data["new_email"] or data["snail_mail"]:
        channels = _plural(len(old_emails), "channel")
        if 0 < len(old_emails) <= 3:
            channels += " (%s)" % ", ".join(old_emails)
        target = data["new_email"].email if data["new_email"] else "snail mail"
        parts.append(
            "Rerouted %s on %s to %s."
            % (_plural(len(foias), "request"), channels, target)
        )
        if data["update_agency_info"]:
            parts.append("Agency contact updated.")
    else:
        parts.append("No contact change.")

    if data["reply"] and foias:
        parts.append("Follow-up queued for %s." % _plural(len(foias), "request"))
    else:
        parts.append("No follow-up sent.")

    resolved = [task for task in tasks if task.resolved]
    if resolved:
        parts.append("Resolved %s." % _plural(len(resolved), "task"))
    still_open = [
        "#%d (%s)" % (task.pk, task.email.email if task.email else "agency-level")
        for task in tasks
        if not task.resolved
    ]
    if len(still_open) == 1:
        parts.append("Task %s is still open." % still_open[0])
    elif still_open:
        parts.append(
            "%d tasks are still open: %s." % (len(still_open), ", ".join(still_open))
        )
    return "%s: %s" % (agency.name, " ".join(parts))


def _error_summary(message, when):
    """What an Error chip says on hover: what failed, and when"""
    if not when:
        return message or "Flagged as an error, no failure on record"
    return "%s — last failed %s" % (
        message or "Failed",
        date_format(timezone.localtime(when), "M j, Y"),
    )


def _latest_fax_errors(phone_ids):
    """The newest fax error per number, in one query"""
    errors = (
        FaxError.objects.filter(recipient_id__in=phone_ids)
        .order_by("recipient_id", "-datetime")
        .distinct("recipient_id")
    )
    return {error.recipient_id: error for error in errors}
