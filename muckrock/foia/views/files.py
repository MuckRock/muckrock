"""FOIA views for handling files"""

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import DetailView

from djangosecure.decorators import frame_deny_exempt

from muckrock.foia.models import FOIAFile, FOIARequest
from muckrock.views import MRFilterableListView

@user_passes_test(lambda u: u.is_staff)
def drag_drop(request):
    """Drag and drop large files into the system"""
    return render(
            request,
            'staff/drag_drop.html',
            {
                'bucket': settings.AWS_AUTOIMPORT_BUCKET_NAME,
                'access_key': settings.AWS_ACCESS_KEY_ID,
                'secret_key': settings.AWS_SECRET_ACCESS_KEY,
            })

@method_decorator(frame_deny_exempt, name='dispatch')
class FileEmbedView(DetailView):
    """Presents an embeddable view for a single file."""
    model = FOIAFile
    template_name = 'foia/file/embed.html'


class FOIAFileListView(MRFilterableListView):
    """Presents a paginated list of files."""
    model = FOIAFile
    template_name = 'foia/file/list.html'
    foia = None

    def dispatch(self, request, *args, **kwargs):
        """Prevent unauthorized users from viewing the files."""
        foia = self.get_foia()
        if not foia.viewable_by(request.user):
            raise Http404()
        return super(FOIAFileListView, self).dispatch(request, *args, **kwargs)

    def get_foia(self):
        """Returns the FOIA Request for the files. Caches it as an attribute."""
        if self.foia is None:
            self.foia = get_object_or_404(FOIARequest, pk=self.kwargs.get('idx'))
        return self.foia

    def get_queryset(self):
        foia = self.get_foia()
        queryset = super(FOIAFileListView, self).get_queryset()
        return (queryset.filter(foia=foia)
            .select_related('foia')
            .select_related('foia__user')
            .select_related('foia__agency')
            .select_related('foia__jurisdiction')
            .prefetch_related('foia__edit_collaborators')
            .prefetch_related('foia__read_collaborators'))

    def get_context_data(self, **kwargs):
        context = super(FOIAFileListView, self).get_context_data(**kwargs)
        context['foia'] = self.get_foia()
        return context
