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
            for error in form.errors.values():
                messages.error(request, error.as_text())
            context = self.get_context_data(object=self.object, repair_form=form)
            return self.render_to_response(context)

        channels = list(
            EmailAddress.objects.filter(pk__in=form.cleaned_data["channel_pks"])
        )
        foias = list(FOIARequest.objects.filter(pk__in=form.cleaned_data["foia_pks"]))
        # Counted before the repair repoints them, and from the selection
        # rather than the tasks matched: a channel covered by the agency level
        # task has no task of its own
        channel_count = len(channels) or len({foia.email_id for foia in foias})
        rerouted = (
            len(foias)
            if form.cleaned_data["new_email"] or form.cleaned_data["snail_mail"]
            else 0
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
        message = "Rerouted %d request%s on %d channel%s for %s." % (
            rerouted,
            "" if rerouted == 1 else "s",
            channel_count,
            "" if channel_count == 1 else "s",
            self.object.name,
        )
        if form.cleaned_data["resolve"]:
            message += " Resolved %d task%s." % (
                len(tasks),
                "" if len(tasks) == 1 else "s",
            )
        messages.success(request, message)
        # Back to the queue, scoped to this agency, where its new blocked total
        # shows whether anything is left before the task can be resolved.
        # Once every task is resolved that view would be empty, so the whole
        # queue it is.
        queue_url = reverse("review-agency-task-list")
        if ReviewAgencyTask.objects.filter(agency=self.object, resolved=False).exists():
            queue_url += "?agency=%d" % self.object.pk
        return redirect(queue_url)


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
