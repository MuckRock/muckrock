"""
Views for tags
"""
from django.http import HttpResponse
from django.views.generic import TemplateView, DetailView

from . import models

def list_all_tags():
    """Should list all tags that exist"""
    tags = models.Tag.objects.all()
    return tags

def filter_tags(filter_string):
    """Should list all tags that match the filter"""
    tags = models.Tag.objects.filter(name__icontains=filter_string)
    return tags

class TagListView(TemplateView):
    """Presents a list of all tags"""
    template_name = 'tags/tag_list.html'

    def get_context_data(self, **kwargs):
        """Adds all tags to context data"""
        context = super(TagListView, self).get_context_data(**kwargs)
        context['tags'] = list_all_tags()
        return context

class TagDetailView(DetailView):
    """Presents the details of a tag"""
    model = models.Tag
    template_name = 'tags/tag_list.html'

    def get_context_data(self, **kwargs):
        """Adds all tags to context data"""
        context = super(TagDetailView, self).get_context_data(**kwargs)
        context['tags'] = list_all_tags()
        return context
