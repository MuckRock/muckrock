"""
URL mappings for the crowdfund application
"""

from django.conf.urls.defaults import patterns, url

from muckrock.crowdfund import views

urlpatterns = patterns('',
    url(r'^project/(?P<slug>[\w\d_-]+)-(?P<pk>\d+)/$', views.project_detail, name='project-detail'),
    )
