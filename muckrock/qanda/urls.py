"""
URL mappings for the Q&A application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object

from qanda.models import Question
from qanda.forms import QuestionForm, AnswerForm

article_args = {'queryset': Question.objects.get_published()}

urlpatterns = patterns('',
        url(r'^$', object_list, {'queryset': Question.objects.all()}, name='question-index'),
        url(r'^new/$', create_object, {'form_class': QuestionForm}, name= 'question-create'),
        url(r'^(?P<slug>[\w\d_-]+)-(?P<object_id>\d+)$', object_detail,
            {'queryset': Question.objects.all()}, name='question-detail'),
        url(r'^(?P<slug>[\w\d_-]+)-(?P<object_id>\d+)/answer$', create_object,
            {'form_class': AnswerForm}, name='answer-create'),
)
