"""FOIA views for handling files"""

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.views.generic import DetailView

from muckrock.foia.models import FOIAFile

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

class FileEmbedView(DetailView):
    """Presents an embeddable view for a single file."""
    model = FOIAFile
    template_name = 'foia/file/embed.html'
    
