"""
URL mappings for the jurisdiction application
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.jurisdiction import views

jur_url = (
    r"(?P<fed_slug>[\w\d_-]+)(?:/(?P<state_slug>[\w\d_-]+))?"
    r"(?:/(?P<local_slug>[\w\d_-]+))?"
)

urlpatterns = [
    re_path(
        r"^$", views.JurisdictionExploreView.as_view(), name="jurisdiction-explore"
    ),
    re_path(
        r"^embed/$", views.JurisdictionEmbedView.as_view(), name="jurisdiction-embed"
    ),
    re_path(r"^list/$", views.List.as_view(), name="jurisdiction-list"),
    re_path(
        r"^%s/exemption/(?P<slug>[\w-]+)-(?P<pk>\d+)/$" % jur_url,
        views.ExemptionDetailView.as_view(),
        name="exemption-detail",
    ),
    re_path(r"^exemptions/$", views.ExemptionListView.as_view(), name="exemption-list"),
    re_path(
        r"^jurisdiction-autocomplete/$",
        views.JurisdictionAutocomplete.as_view(),
        name="jurisdiction-autocomplete",
    ),
    re_path(
        r"^jurisdiction-state-inclusive-autocomplete/$",
        views.JurisdictionStateInclusiveAutocomplete.as_view(),
        name="jurisdiction-state-inclusive-autocomplete",
    ),
    re_path(r"^%s/$" % jur_url, views.detail, name="jurisdiction-detail"),
]
