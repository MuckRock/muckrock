"""Views for handling communications"""

# Django
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView

# Third Party
from furl import furl

# MuckRock
from muckrock.core.views import MRListView, class_view_decorator
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


class FOIACommunicationDirectAgencyView(RedirectView):
    """View to redirect agency users to communication"""

    def get_redirect_url(self, *args, **kwargs):
        """Get the anchor to the communication and append a parameter to
        signify this is an agency viewer
        """
        communication = get_object_or_404(FOIACommunication, pk=kwargs["idx"])
        url = furl(communication.get_absolute_url())
        url.args["agency"] = 1
        return url.url
