"""
Views for tags
"""
from django.http import HttpResponse
from django.views.generic import View

from . import models

def list_all_tags():
    """Should list all tags that exist"""
    tags = models.Tag.objects.all()
    return tags

class TagListView(View):
    """Presents a list of all tags"""
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, World')
