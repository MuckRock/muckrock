"""
URL mappings for the Q&A application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list, object_detail

from qanda.models import Question

article_args = {'queryset': Question.objects.get_published()}

urlpatterns = patterns('',
        url(r'^$', object_list, {'queryset': Question.objects.all()}, name='question-index'),
        url(r'(?P<slug>[\w\d_-]+)-(?P<object_id>\d+)^$', object_detail,
            {'queryset': Question.objects.all()}, name='question-detail'),
)
