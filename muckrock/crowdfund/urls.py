"""
URL mappings for the crowdfund application
"""

from django.conf.urls import patterns, url

from muckrock.crowdfund import views

urlpatterns = patterns(
    '',
    url(r'^request/(?P<pk>\d+)/$',
        views.CrowdfundRequestDetail.as_view(),
        name='crowdfund-request'),
    url(r'^project/(?P<slug>[\w\d_-]+)-(?P<pk>\d+)/$',
        views.project_detail,
        name='project-detail'),
)
