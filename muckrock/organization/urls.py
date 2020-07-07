"""
URL mappings for the Organization application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.organization import views

urlpatterns = [
    url(r"^$", views.OrganizationListView.as_view(), name="org-index"),
    url(r"^activate/$", views.activate, name="org-activate"),
    url(
        r"^(?P<slug>[\w-]+)/$",
        views.OrganizationDetailView.as_view(),
        name="org-detail",
    ),
    url(
        r"^(?P<slug>[\w-]+)/update/$",
        views.OrganizationSquareletView.as_view(),
        name="org-squarelet",
    ),
]
