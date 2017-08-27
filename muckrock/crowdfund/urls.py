"""
URL mappings for the crowdfund application
"""

from django.conf.urls import url

from muckrock.crowdfund import views

urlpatterns = [
    url(r'^$',
        views.CrowdfundListView.as_view(),
        name='crowdfund-list'),
    url(r'^(?P<pk>\d+)/$',
        views.CrowdfundDetailView.as_view(),
        name='crowdfund'),
    url(r'^(?P<pk>\d+)/embed/$',
        views.CrowdfundEmbedView.as_view(),
        name='crowdfund-embed'),
    ]
