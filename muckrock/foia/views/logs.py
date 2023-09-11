"""Views for FOIA Logs"""

# Django
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import FormView

# MuckRock
from muckrock.agency.models.agency import Agency
from muckrock.core.views import MRSearchFilterListView
from muckrock.foia.filters import FOIALogFilterSet
from muckrock.foia.forms.logs import FOIALogUploadForm
from muckrock.foia.importers import import_logs
from muckrock.foia.models.log import FOIALog


class FOIALogUploadView(UserPassesTestMixin, FormView):
    """View to upload a CSV to import FOIA Logs"""

    form_class = FOIALogUploadForm
    template_name = "foia/upload_logs.html"

    def test_func(self):
        """User must be staff"""
        return self.request.user.is_staff

    def get_success_url(self):
        """Return to same page"""
        return reverse("foia-log-upload")

    def form_valid(self, form):
        """Import on succesful upload"""
        num = import_logs(form.cleaned_data["agency"], form.cleaned_data["log"])
        messages.success(self.request, f"Import succesful - {num} logs imported")
        return super().form_valid(form)


class FOIALogDetail(DetailView):
    """Details of a single FOIA Log"""

    model = FOIALog
    context_object_name = "foia_log"
    pk_url_kwarg = "idx"
    template_name = "foia/foia_log/detail.html"


class FOIALogList(MRSearchFilterListView):
    """Filterable list of FOIA logs"""

    model = FOIALog
    template_name = "foia/foia_log/list.html"
    foia = None
    filter_class = FOIALogFilterSet
    title = "FOIA Logs"
    default_sort = "date_requested"
    default_order = "desc"

    def get_queryset(self):
        """Select related agency and jurisdiction to avoid extra queries"""
        return super().get_queryset().select_related("agency__jurisdiction")


class FOIALogLanding(TemplateView):
    """Landing page that introduces FOIA logs"""

    template_name = "foia/foia_log/explore.html"

    def get_context_data(self, **kwargs):
        """Adds educational content and suggested searches"""
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "log_count": FOIALog.objects.count(),
            "agency_count": Agency.objects.with_logs().count(),
        }
        return context
