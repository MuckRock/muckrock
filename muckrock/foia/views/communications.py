"""Views for handling communications"""

# Django
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView

# Third Party
from furl import furl

# MuckRock
from muckrock.core.views import MRListView, class_view_decorator
from muckrock.foia.forms.comms import AgencyPasscodeForm
from muckrock.foia.models import FOIACommunication


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class AdminCommunicationView(MRListView):
    """View for admins to see the latest communications"""

    model = FOIACommunication
    title = "All Communications"
    template_name = "foia/communication/list.html"

    def get_queryset(self):
        """Sort by reverse datetime"""
        return (
            super()
            .get_queryset()
            .order_by("-datetime")
            .preload_list()
            .select_related("foia__agency__jurisdiction", "from_user__profile__agency")
        )


class FOIACommunicationDirectAgencyView(SingleObjectMixin, FormView):
    """View to redirect agency users to communication"""

    form_class = AgencyPasscodeForm
    model = FOIACommunication
    pk_url_kwarg = "idx"
    template_name = "foia/communication/agency.html"

    def get_success_url(self):
        """URL for the communication, with a parameter marking this is an agency user"""
        url = furl(self.object.get_absolute_url())
        url.args["agency"] = 1
        return url.url

    def get(self, request, *args, **kwargs):
        """Check if the communication requires a passcode"""
        self.object = self.get_object()

        if self.object.foia.has_perm(request.user, "view"):
            return redirect(self.get_success_url())

        key = f"foiapasscode:{self.object.foia.pk}"
        if key in request.session:
            form = AgencyPasscodeForm({"passcode": request.session[key]})
            if form.is_valid():
                return redirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Save the passcode to the session"""
        self.request.session[f"foiapasscode:{self.object.foia.pk}"] = form.cleaned_data[
            "passcode"
        ]
        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        """Pass the communication to the form"""
        kwargs = super().get_form_kwargs()
        kwargs.update({"communication": self.object})
        return kwargs
