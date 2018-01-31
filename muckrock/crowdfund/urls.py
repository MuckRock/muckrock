"""
URL mappings for the crowdfund application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.crowdfund import views

urlpatterns = [
    url(r'^$', views.CrowdfundListView.as_view(), name='crowdfund-list'),
    url(
        r'^(?P<pk>\d+)/$',
        views.CrowdfundDetailView.as_view(),
        name='crowdfund'
    ),
    url(
        r'^(?P<pk>\d+)/embed/$',
        views.CrowdfundEmbedView.as_view(),
        name='crowdfund-embed'
    ),
]
