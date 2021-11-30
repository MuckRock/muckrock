"""
URL routes for the project application
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.project import views

urlpatterns = [
    re_path(r"^$", views.ProjectExploreView.as_view(), name="project"),
    re_path(r"^list/$", views.ProjectListView.as_view(), name="project-list"),
    re_path(
        r"^contributor/(?P<username>[\w\-.@+ ]+)/$",
        views.ProjectContributorView.as_view(),
        name="project-contributor",
    ),
    re_path(r"^create/$", views.ProjectCreateView.as_view(), name="project-create"),
    re_path(
        r"^(?P<slug>[\w-]+)-(?P<pk>\d+)/$",
        views.ProjectDetailView.as_view(),
        name="project-detail",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)-(?P<pk>\d+)/edit/$",
        views.ProjectEditView.as_view(),
        name="project-edit",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)-(?P<pk>\d+)/publish/$",
        views.ProjectPublishView.as_view(),
        name="project-publish",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)-(?P<pk>\d+)/crowdfund/$",
        views.ProjectCrowdfundView.as_view(),
        name="project-crowdfund",
    ),
    re_path(
        r"^project-autocomplete/$",
        views.ProjectAutocomplete.as_view(),
        name="project-autocomplete",
    ),
]
