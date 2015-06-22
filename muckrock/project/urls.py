"""
URL routes for the project application
"""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required, user_passes_test

from muckrock.project import views

urlpatterns = patterns('',
    url(r'^create/$',
        views.ProjectCreateView.as_view(),
        name='project-create'),
    url(r'^(?P<slug>[\w-]+)/$',
        views.ProjectDetailView.as_view(),
        name='project-detail'),
    url(r'^(?P<slug>[\w-]+)/update/$',
        login_required(views.ProjectUpdateView.as_view()),
        name='project-update'),
    url(r'^(?P<slug>[\w-]+)/delete/$',
        login_required(views.ProjectDeleteView.as_view()),
        name='project-delete')
)
