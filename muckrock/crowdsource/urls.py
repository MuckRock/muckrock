"""
URL mappings for the crowdsource app
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.crowdsource import views

urlpatterns = [
    re_path(
        r"^(?P<slug>[-\w]+)-(?P<idx>\d+)/$",
        views.CrowdsourceDetailView.as_view(),
        name="crowdsource-detail",
    ),
    re_path(
        r"^(?P<slug>[-\w]+)-(?P<idx>\d+)/draft/$",
        views.CrowdsourceUpdateView.as_view(),
        name="crowdsource-draft",
    ),
    re_path(
        r"^(?P<slug>[-\w]+)-(?P<idx>\d+)/form/$",
        views.CrowdsourceFormView.as_view(),
        name="crowdsource-assignment",
    ),
    re_path(
        r"^(?P<slug>[-\w]+)-(?P<idx>\d+)/embed/$",
        views.CrowdsourceEmbededFormView.as_view(),
        name="crowdsource-embed",
    ),
    re_path(
        r"^(?P<slug>[-\w]+)-(?P<idx>\d+)/gallery/$",
        views.CrowdsourceEmbededGallery.as_view(),
        name="crowdsource-gallery",
    ),
    re_path(
        r"^confirm/$",
        views.CrowdsourceEmbededConfirmView.as_view(),
        name="crowdsource-embed-confirm",
    ),
    re_path(r"^$", views.CrowdsourceExploreView.as_view(), name="crowdsource-index"),
    re_path(r"^list/$", views.CrowdsourceListView.as_view(), name="crowdsource-list"),
    re_path(
        r"^create/$", views.CrowdsourceCreateView.as_view(), name="crowdsource-create"
    ),
    re_path(r"^oembed/$", views.oembed, name="crowdsource-oembed"),
    re_path(r"^message/$", views.message_response, name="crowdsource-message-response"),
    re_path(
        r"^(?P<idx>\d+)/edit/$",
        views.CrowdsourceEditResponseView.as_view(),
        name="crowdsource-edit-response",
    ),
    re_path(
        r"^(?P<idx>\d+)/revert/$",
        views.CrowdsourceRevertResponseView.as_view(),
        name="crowdsource-revert-response",
    ),
    re_path(
        r"^crowdsource-autocomplete/$",
        views.CrowdsourceAutocomplete.as_view(),
        name="crowdsource-autocomplete",
    ),
]
