"""
Views for tags
"""
from django.http import HttpResponse
from django.views.generic import View

class TagListView(View):
    """Presents a list of all tags"""
    def get(self, request, *args, **kwargs):
        return HttpResponse('Hello, World')
