"""Viewsets for Agency"""

# Third Party
import django_filters
from rest_framework import filters, viewsets

# MuckRock
from muckrock.agency.api_v2.serializers import AgencySerializer
from muckrock.agency.models import Agency
from muckrock.core.views import AuthenticatedAPIMixin

# pylint: disable=too-few-public-methods, too-many-ancestors
class AgencyViewSet(viewsets.ReadOnlyModelViewSet, AuthenticatedAPIMixin):
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
    ]

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""

        jurisdiction__id = django_filters.NumberFilter(
            field_name="jurisdiction__id", label="Jurisdiction ID"
        )
        name = django_filters.CharFilter(
            field_name="name", lookup_expr="icontains", label="Agency Name"
        )

        class Meta:
            """Filters"""

            model = Agency
            fields = ("name", "jurisdiction__id")

    filterset_class = Filter
