"""
URL routes for the project application
"""

from django.conf.urls import patterns, url

from muckrock.project import views

urlpatterns = patterns('',
    url(r'^$',
        views.ProjectExploreView.as_view(),
        name='project'),
    url(r'^list/$',
        views.ProjectListView.as_view(),
        name='project-list'),
    url(r'^create/$',
        views.ProjectCreateView.as_view(),
        name='project-create'),
    url(r'^(?P<slug>[\w-]+)-(?P<pk>\d+)/$',
        views.ProjectDetailView.as_view(),
        name='project-detail'),
    url(r'^(?P<slug>[\w-]+)-(?P<pk>\d+)/edit/$',
        views.ProjectEditView.as_view(),
        name='project-edit'),
    url(r'^(?P<slug>[\w-]+)-(?P<pk>\d+)/publish/$',
        views.ProjectPublishView.as_view(),
        name='project-publish'),
    url(r'^(?P<slug>[\w-]+)-(?P<pk>\d+)/crowdfund/$',
        views.ProjectCrowdfundView.as_view(),
        name='project-crowdfund'),
)
