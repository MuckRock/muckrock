"""
URL mappings for the Q&A application
"""

from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from muckrock.qanda import views
from muckrock.qanda.feeds import LatestQuestions

# pylint: disable=no-value-for-parameter

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.QuestionList.as_view(),
        name='question-index'
    ),
    url(
        r'^unanswered/$',
        views.UnansweredQuestionList.as_view(),
        name='question-unanswered'
    ),
    url(
        r'^recent/$',
        RedirectView.as_view(url='/questions/?sort=answer_date&order=desc'),
        name='question-recent'
    ),
    url(
        r'^new/$',
        views.create_question,
        name='question-create'
    ),
    url(
        r'^follow-new/$',
        views.follow_new,
        name='question-follow-new'
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
        r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/follow$',
        views.follow,
        name='question-follow'
    ),
    url(
        r'^feed/$',
        LatestQuestions(),
        name='question-feed'
    ),
)
