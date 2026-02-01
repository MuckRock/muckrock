"""Views for handling communications"""

# Django
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView

# Third Party
from furl import furl

# MuckRock
from muckrock.core.views import MRFilterCursorListView, class_view_decorator
from muckrock.foia.filters import FOIACommunicationFilterSet
from muckrock.foia.forms.comms import AgencyEmailLinkForm
from muckrock.foia.models import FOIACommunication


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class AdminCommunicationView(MRFilterCursorListView):
    """View for admins to see the latest communications"""

    model = FOIACommunication
    title = "All Communications"
    template_name = "foia/communication/list.html"
    filter_class = FOIACommunicationFilterSet

    def get_queryset(self):
        """Sort by reverse primary key"""
        return (
            super()
            .get_queryset()
            .order_by("-pk")
            .preload_list()
            .prefetch_related(
                "foia__agency__jurisdiction", "from_user__profile__agency"
            )
        )


class FOIACommunicationDirectAgencyView(SingleObjectMixin, FormView):
    """View to redirect agency users to communication

    If the request is not embargoed, this just redirects to the request
    If it is embargoed, this displays the form for the agency user to obtain
    a login link so they may view and directly upload to the request.
    """

    form_class = AgencyEmailLinkForm
    model = FOIACommunication
    pk_url_kwarg = "idx"
    template_name = "foia/communication/agency.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = None

    def get(self, request, *args, **kwargs):
        """Check if the communication requires a passcode"""
        self.object = self.get_object()

        if self.object.foia.has_perm(request.user, "view"):
            url = furl(self.object.get_absolute_url())
            url.args["agency"] = 1
            return redirect(url.url)

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Send the email the login link"""
        form.send_link()
        return redirect("communication-direct-agency", idx=self.object.pk)

    def get_form_kwargs(self):
        """Pass the request to the form"""
        kwargs = super().get_form_kwargs()
        kwargs.update({"foia": self.object.foia})
        return kwargs
