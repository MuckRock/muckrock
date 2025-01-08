"""
Provides Jurisdiction application API views
"""

# Third Party
import django_filters
from rest_framework import viewsets

# MuckRock
from muckrock.jurisdiction.api_v2.serializers import JurisdictionSerializer
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.core.views import AuthenticatedAPIMixin

# pylint: disable=too-few-public-methods
class JurisdictionViewSet(viewsets.ReadOnlyModelViewSet, AuthenticatedAPIMixin):
    """API views for Jurisdiction"""

    queryset = Jurisdiction.objects.order_by("id").select_related("parent__parent")
    serializer_class = JurisdictionSerializer
    ordering_fields = ["abbrev", "level", "name"]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)

    class JurisdictionFilter(django_filters.FilterSet):
        """API Filters for Jurisdictions"""

        parent = django_filters.NumberFilter(
            field_name="parent__id",
            label=(
                "ID of the parent jurisdiction. This defines the hierarchy between jurisdictions, "
                "where a jurisdiction can have a federal or state parent. "
                "Local jurisdictions cannot be parents."
            ),
        )
        name = django_filters.CharFilter(
            field_name="name",
            lookup_expr="icontains",
            label="The name of the jurisdiction.",
        )
        abbrev = django_filters.CharFilter(
            field_name="abbrev",
            lookup_expr="iexact",
            label="The abbreviation for the jurisdiction.  Local jurisdictions don't have one.",
        )
        level = django_filters.CharFilter(
            field_name="level", label="The level of the jurisdiction."
        )

        class Meta:
            """List of filters for the API"""

            model = Jurisdiction
            fields = ("abbrev", "level", "name")

    filterset_class = JurisdictionFilter
