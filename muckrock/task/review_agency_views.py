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
from django.views.generic import DetailView

# MuckRock
from muckrock.agency.models import Agency
from muckrock.communication.models import EmailAddress
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

        # Demoted behind a disclosure but reachable -- mail and phone crowd out
        # what is actually broken when they share the main reading.
        context["faxes"] = agency.agencyphone_set.filter(
            phone__type="fax"
        ).select_related("phone")
        context["phones"] = agency.agencyphone_set.filter(
            phone__type="phone"
        ).select_related("phone")
        context["addresses"] = agency.agencyaddress_set.select_related("address")

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

        channels = EmailAddress.objects.filter(pk__in=form.cleaned_data["channel_pks"])
        foias = FOIARequest.objects.filter(pk__in=form.cleaned_data["foia_pks"])

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
            "Repaired %d channel%s for %s."
            % (len(tasks), "" if len(tasks) == 1 else "s", self.object.name),
        )
        return redirect(reverse("review-agency-detail", kwargs={"pk": self.object.pk}))
