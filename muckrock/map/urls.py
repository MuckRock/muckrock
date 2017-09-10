"""
URL mappings for the Map application
"""

from django.conf.urls import url

from muckrock.map.views import MapListView, MapDetailView, MapLayerView

urlpatterns = [
    url(r'^$', MapListView.as_view(), name='map-list'),
    url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/$',
        MapDetailView.as_view(),
        name='map-detail'),
    url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/data.geojson$',
        MapLayerView.as_view(),
        name='map-data'),
    ]
