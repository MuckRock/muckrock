"""
URL mappings for the Map application
"""

from django.conf.urls import patterns, url

from muckrock.map.models import Map, Marker
from muckrock.map.views import MapListView, MapDetailView, MapLayerView

urlpatterns = patterns('',
    url(r'^$', MapListView.as_view(), name='map-list'),
    url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/$',
        MapDetailView.as_view(),
        name='map-detail'),
    url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/data.geojson$',
        MapLayerView.as_view(),
        name='map-data'),
)
