"""
URL mappings for the Q&A application
"""

from django.conf.urls import patterns, url

from muckrock.qanda import views
from muckrock.qanda.feeds import LatestQuestions

# pylint: disable=E1120

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.List.as_view(template_name='lists/question_list.html'),
        name='question-index'
    ),
    url(
        r'^unanswered/$',
        views.ListUnanswered.as_view(template_name='lists/question_list.html'),
        name='question-unanswered'
    ),
    url(
        r'^recent/$',
        views.ListRecent.as_view(template_name='lists/question_list.html'),
        name='question-recent'
    ),
    url(
        r'^new/$',
        views.create_question,
        name='question-create'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)-(?P<pk>\d+)$',
        views.Detail.as_view(template_name='details/question_detail.html'),
        name='question-detail'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/answer$',
        views.create_answer,
        name='answer-create'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/change-follow$',
        views.follow,
        name='question-follow'
    ),
    url(
        r'^change-subscription/$',
        views.subscribe,
        name='question-subscribe'
    ),
    url(
        r'^feed/$',
        LatestQuestions(),
        name='question-feed'
    ),
)
