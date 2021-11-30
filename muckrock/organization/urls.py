"""
URL mappings for the Organization application
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.organization import views

urlpatterns = [
    re_path(r"^$", views.OrganizationListView.as_view(), name="org-index"),
    re_path(r"^activate/$", views.activate, name="org-activate"),
    re_path(
        r"^(?P<slug>[\w-]+)/$",
        views.OrganizationDetailView.as_view(),
        name="org-detail",
    ),
    re_path(
        r"^(?P<slug>[\w-]+)/update/$",
        views.OrganizationSquareletView.as_view(),
        name="org-squarelet",
    ),
]
