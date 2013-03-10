"""
URL mappings for the Q&A application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.list import ListView

from qanda import views
from qanda.models import Question

# pylint: disable=E1120

urlpatterns = patterns('',
        url(r'^$',              ListView.as_view(model=Question), name='question-index'),
        url(r'^new/$',          views.create_question, name='question-create'),
        url(r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)$',
                                views.question_detail, name='question-detail'),
        url(r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/answer$',
                                views.create_answer, name='answer-create'),
)
