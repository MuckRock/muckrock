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
)
