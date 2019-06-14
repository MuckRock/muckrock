"""
URL mappings for the crowdsource app
"""

# Django
from django.conf.urls import url
from django.views.generic.base import RedirectView

# MuckRock
from muckrock.crowdsource import views

urlpatterns = [
    url(
        r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/$',
        views.CrowdsourceDetailView.as_view(),
        name='crowdsource-detail',
    ),
    url(
        r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/draft/$',
        views.CrowdsourceUpdateView.as_view(),
        name='crowdsource-draft',
    ),
    url(
        r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/form/$',
        views.CrowdsourceFormView.as_view(),
        name='crowdsource-assignment',
    ),
    url(
        r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/embed/$',
        views.CrowdsourceEmbededFormView.as_view(),
        name='crowdsource-embed',
    ),
    url(
        r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/gallery/$',
        views.CrowdsourceEmbededGallery.as_view(),
        name='crowdsource-gallery',
    ),
    url(
        r'^confirm/$',
        views.CrowdsourceEmbededConfirmView.as_view(),
        name='crowdsource-embed-confirm',
    ),
    url(
        r'^$',
        views.CrowdsourceExploreView.as_view(),
        name='crowdsource-index',
    ),
    url(
        r'^list/$',
        views.CrowdsourceListView.as_view(),
        name='crowdsource-list',
    ),
    url(
        r'^create/$',
        views.CrowdsourceCreateView.as_view(),
        name='crowdsource-create',
    ),
    url(
        r'^oembed/$',
        views.oembed,
        name='crowdsource-oembed',
    ),
    url(
        r'^message/$',
        views.message_response,
        name='crowdsource-message-response',
    ),
    url(
        r'^(?P<idx>\d+)/edit/$',
        views.CrowdsourceEditResponseView.as_view(),
        name='crowdsource-edit-response',
    ),
    url(
        r'^(?P<idx>\d+)/revert/$',
        views.CrowdsourceRevertResponseView.as_view(),
        name='crowdsource-revert-response',
    ),
]
