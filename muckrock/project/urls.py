"""
URL routes for the project application
"""

from django.conf.urls import patterns, url

from muckrock.crowdfund.views import CrowdfundProjectCreateView
from muckrock.project import views

urlpatterns = patterns('',
    url(r'^$',
        views.ProjectListView.as_view(),
        name='project-create'),
    url(r'^create/$',
        views.ProjectCreateView.as_view(),
        name='project-create'),
    url(r'^(?P<slug>[\w-]+)-(?P<id>\d+)/$',
        views.ProjectDetailView.as_view(),
        name='project-detail'),
    url(r'^(?P<slug>[\w-]+)-(?P<id>\d+)/update/$',
        views.ProjectUpdateView.as_view(),
        name='project-update'),
    url(r'^(?P<slug>[\w-]+)-(?P<id>\d+)/delete/$',
        views.ProjectDeleteView.as_view(),
        name='project-delete'),
    url(r'^(?P<slug>[\w-]+)-(?P<id>\d+)/crowdfund/$',
        CrowdfundProjectCreateView.as_view(),
        name='project-crowdfund'),
)
