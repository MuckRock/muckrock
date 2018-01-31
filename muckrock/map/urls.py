"""
URL mappings for the Map application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.map.views import MapDetailView, MapLayerView, MapListView

urlpatterns = [
    url(r'^$', MapListView.as_view(), name='map-list'),
    url(
        r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/$',
        MapDetailView.as_view(),
        name='map-detail'
    ),
    url(
        r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/data.geojson$',
        MapLayerView.as_view(),
        name='map-data'
    ),
]
