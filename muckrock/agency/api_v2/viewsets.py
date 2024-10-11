"""Viewsets for Agency"""

# Third Party
import django_filters
from rest_framework import viewsets
from rest_framework import filters

# MuckRock
from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer

# pylint: disable=too-few-public-methods
class AgencyViewSet(viewsets.ReadOnlyModelViewSet):
    """API views for Agency"""

    queryset = Agency.objects.order_by("id")
    serializer_class = AgencySerializer

    # Limit ordering fields to just name and status
    ordering_fields = ["name", "status"]

    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    ]
    search_fields = [
        "name",
        "jurisdiction__name",
    ]

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""

        jurisdiction = django_filters.CharFilter(
            field_name="jurisdiction__name", lookup_expr="icontains"
        )
        name = django_filters.CharFilter(
            field_name="name", lookup_expr="icontains"
        )

        class Meta:
            """ Filters """
            model = Agency
            fields = ("name", "jurisdiction__name")

    filterset_class = Filter
