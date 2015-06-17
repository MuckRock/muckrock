"""
URL routes for the project application
"""

from django.conf.urls import patterns, url

from muckrock.project import views

urlpatterns = patterns('',
    url(r'^create/$', views.CreateProjectView.as_view(), name='project-create'),
)
