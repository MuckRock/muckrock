"""FOIA views for handling files"""

# Django
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView

# MuckRock
from muckrock.core.views import ModelFilterMixin, MRListView
from muckrock.foia.filters import FOIAFileFilterSet
from muckrock.foia.models import FOIAFile, FOIARequest


@method_decorator(xframe_options_exempt, name="dispatch")
class FileEmbedView(DetailView):
    """Presents an embeddable view for a single file."""

    model = FOIAFile
    queryset = FOIAFile.objects.filter(comm__foia__embargo=False)
    template_name = "foia/file/embed.html"


class FOIAFileListView(ModelFilterMixin, MRListView):
    """Presents a paginated list of files."""

    model = FOIAFile
    template_name = "foia/file/list.html"
    foia = None
    filter_class = FOIAFileFilterSet

    def dispatch(self, request, *args, **kwargs):
        """Prevent unauthorized users from viewing the files."""
        foia = self.get_foia()
        if not foia.has_perm(request.user, "view"):
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_foia(self):
        """Returns the FOIA Request for the files. Caches it as an attribute."""
        if self.foia is None:
            self.foia = get_object_or_404(FOIARequest, pk=self.kwargs.get("idx"))
        return self.foia

    def get_queryset(self):
        """Only files for one FOIA request"""
        foia = self.get_foia()
        queryset = super().get_queryset()
        return queryset.filter(comm__foia=foia).select_related("comm__foia")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["foia"] = self.get_foia()
        context["foia_url"] = context["foia"].get_absolute_url()
        return context
