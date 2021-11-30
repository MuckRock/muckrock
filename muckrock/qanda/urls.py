"""
URL mappings for the Q&A application
"""

# Django
from django.urls import re_path
from django.views.generic.base import RedirectView

# MuckRock
from muckrock.qanda import views
from muckrock.qanda.feeds import LatestQuestions

# pylint: disable=no-value-for-parameter

urlpatterns = [
    re_path(r"^$", views.QuestionList.as_view(), name="question-index"),
    re_path(
        r"^unanswered/$",
        RedirectView.as_view(url="/questions/?unanswered=on"),
        name="question-unanswered",
    ),
    re_path(
        r"^recent/$",
        RedirectView.as_view(url="/questions/?sort=answer_date&order=desc"),
        name="question-recent",
    ),
    re_path(
        r"^report-spam/(?P<model>(?:question)|(?:answer))/(?P<model_pk>\d+)/$",
        views.report_spam,
        name="question-spam",
    ),
    re_path(
        r"^block-user/(?P<model>(?:question)|(?:answer))/(?P<model_pk>\d+)/$",
        views.block_user,
        name="question-block",
    ),
    re_path(
        r"^(?P<slug>[\w\d_-]+)-(?P<pk>\d+)/$",
        views.Detail.as_view(template_name="qanda/detail.html"),
        name="question-detail",
    ),
    re_path(
        r"^(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/follow/$",
        views.follow,
        name="question-follow",
    ),
    re_path(r"^feed/$", LatestQuestions(), name="question-feed"),
]
