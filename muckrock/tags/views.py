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

def filter_tags(filter_string):
    """Should list all tags that match the filter"""
    tags = models.Tag.objects.filter(name__icontains=filter_string)
    return tags

class TagListView(View):
    """Presents a list of all tags"""
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, World')
