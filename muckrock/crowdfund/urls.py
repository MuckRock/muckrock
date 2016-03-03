"""
URL mappings for the crowdfund application
"""

from django.conf.urls import patterns, url

from muckrock.crowdfund import views

urlpatterns = patterns(
    '',
    url(r'^$',
        views.CrowdfundListView.as_view(),
        name='crowdfund-list'),
    url(r'^(?P<pk>\d+)/$',
        views.CrowdfundDetailView.as_view(),
        name='crowdfund'),
)
