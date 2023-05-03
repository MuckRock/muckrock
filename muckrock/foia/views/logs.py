"""Views for FOIA Logs"""

# Django
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from django.views.generic.edit import FormView

# MuckRock
from muckrock.foia.forms.logs import FOIALogUploadForm
from muckrock.foia.importers import import_logs


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
