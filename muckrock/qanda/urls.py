"""
URL mappings for the Q&A application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list

from muckrock.qanda import views
from muckrock.qanda.models import Question

urlpatterns = patterns('',
        url(r'^$',              object_list, {'queryset': Question.objects.all()},
                                name='question-index'),
        url(r'^new/$',          views.create_question, name='question-create'),
        url(r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)$',
                                views.question_detail, name='question-detail'),
        url(r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/answer$',
                                views.create_answer, name='answer-create'),
)
