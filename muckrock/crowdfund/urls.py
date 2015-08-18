"""
URL mappings for the crowdfund application
"""

from django.conf.urls import patterns, url

from muckrock.crowdfund import views

urlpatterns = patterns(
    '',
    url(r'^request/$',
        views.CrowdfundRequestListView.as_view(),
        name='crowdfund-request-list'),
    url(r'^request/(?P<pk>\d+)/$',
        views.CrowdfundRequestDetail.as_view(),
        name='crowdfund-request'),
    url(r'^project/(?P<pk>\d+)/$',
        views.CrowdfundProjectDetail.as_view(),
        name='crowdfund-project'),
)
