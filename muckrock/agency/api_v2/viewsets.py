"""Viewsets for Agency"""

# Third Party
import django_filters
from rest_framework import viewsets
from rest_framework import filters

# MuckRock
from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer

# pylint: disable=R0901
class AgencyViewSet(viewsets.ReadOnlyModelViewSet):
    """API views for Agency"""

    queryset = (Agency.objects.order_by("id"))

    serializer_class = AgencySerializer
    # Don't allow ordering by computed fields
    ordering_fields = [
        f
        for f in serializer_class.Meta.fields
        if f
        not in ("absolute_url", "average_response_time", "fee_rate", "success_rate")
        and not f.startswith(("has_", "number_"))
    ]
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    ]
    search_fields = [
        "name",
        "jurisdiction__name",
    ]  # Added jurisdiction name to search fields

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""

        jurisdiction = django_filters.CharFilter(
            field_name="jurisdiction__name", lookup_expr="icontains"
        )
        name = django_filters.CharFilter(
            field_name="name", lookup_expr="icontains"  # Allows case-insensitive filtering by name
        )

        # pylint: disable=R0903
        class Meta:
            """Meta options for filtering agencies."""
            model = Agency
            fields = ("name", "jurisdiction__name")

    filterset_class = Filter

    def get_queryset(self):
        """Filter out non-approved agencies for non-staff"""
        queryset = super().get_queryset()
        jurisdiction = self.request.query_params.get("jurisdiction", None)
        name = self.request.query_params.get("name", None)

        if jurisdiction:
            queryset = queryset.filter(jurisdiction__name__icontains=jurisdiction)

        if name:
            queryset = queryset.filter(name__icontains=name)

        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(status="approved")
