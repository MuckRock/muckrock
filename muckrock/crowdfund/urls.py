"""
URL mappings for the crowdfund application
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.crowdfund import views

urlpatterns = [
    re_path(r"^$", views.CrowdfundListView.as_view(), name="crowdfund-list"),
    re_path(r"^(?P<pk>\d+)/$", views.CrowdfundDetailView.as_view(), name="crowdfund"),
    re_path(
        r"^(?P<pk>\d+)/embed/$",
        views.CrowdfundEmbedView.as_view(),
        name="crowdfund-embed",
    ),
]
