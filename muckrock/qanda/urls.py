"""
URL mappings for the Q&A application
"""

# Django
from django.conf.urls import url
from django.views.generic.base import RedirectView

# MuckRock
from muckrock.qanda import views
from muckrock.qanda.feeds import LatestQuestions

# pylint: disable=no-value-for-parameter

urlpatterns = [
    url(r'^$', views.QuestionList.as_view(), name='question-index'),
    url(
        r'^unanswered/$',
        RedirectView.as_view(url='/questions/?unanswered=on'),
        name='question-unanswered'
    ),
    url(
        r'^recent/$',
        RedirectView.as_view(url='/questions/?sort=answer_date&order=desc'),
        name='question-recent'
    ),
    url(r'^new/$', views.create_question, name='question-create'),
    url(r'^follow-new/$', views.follow_new, name='question-follow-new'),
    url(
        r'^report-spam/(?P<model>(?:question)|(?:answer))/(?P<model_pk>\d+)/$',
        views.report_spam,
        name='question-spam'
    ),
    url(
        r'^block-user/(?P<model>(?:question)|(?:answer))/(?P<model_pk>\d+)/$',
        views.block_user,
        name='question-block'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)-(?P<pk>\d+)/$',
        views.Detail.as_view(template_name='qanda/detail.html'),
        name='question-detail'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/answer/$',
        views.create_answer,
        name='answer-create'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/follow/$',
        views.follow,
        name='question-follow'
    ),
    url(r'^feed/$', LatestQuestions(), name='question-feed'),
]
