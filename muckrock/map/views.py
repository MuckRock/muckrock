"""
Views for the Map application
"""

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.views.generic import DetailView, ListView, View
from django.utils.decorators import method_decorator

from djgeojson.serializers import Serializer as GeoJSONSerializer

from muckrock.map.models import Map, Marker

user_can_view_maps = lambda u: u.is_authenticated() and u.profile.experimental

class MapDetailView(DetailView):
    """Limits map detail view to experimental for now."""
    model = Map

    @method_decorator(user_passes_test(user_can_view_maps))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(MapDetailView, self).dispatch(*args, **kwargs)


class MapListView(ListView):
    """Limits map list view to staff for now."""
    model = Map

    @method_decorator(user_passes_test(user_can_view_maps))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(MapListView, self).dispatch(*args, **kwargs)


class MapLayerView(View):
    """Serializes map data to a GeoJSON file."""
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        map = Map.objects.get(id=kwargs['idx'])
        data = GeoJSONSerializer().serialize(
            Marker.objects.filter(map=map),
            geometry_field='point',
            use_natural_keys=True,
            with_modelname=False
        )
        return HttpResponse(data, content_type='application/json')
