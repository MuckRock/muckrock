"""
Provides Jurisdiction application API views
"""

# Third Party
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

# MuckRock
from muckrock.core.pagination import APIV2CursorPagination
from muckrock.core.views import AuthenticatedAPIMixin
from muckrock.jurisdiction.api_v2.serializers import JurisdictionSerializer
from muckrock.jurisdiction.models import Jurisdiction


# pylint: disable=too-few-public-methods
class JurisdictionViewSet(AuthenticatedAPIMixin, viewsets.ReadOnlyModelViewSet):
    """API views for Jurisdiction"""

    queryset = Jurisdiction.objects.select_related("parent")
    serializer_class = JurisdictionSerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = APIV2CursorPagination

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
        parent_name = django_filters.CharFilter(
            field_name="parent__name",
            lookup_expr="icontains",
            label="The name of the parent jurisdiction.",
        )
        parent_abbrev = django_filters.CharFilter(
            field_name="parent__abbrev",
            lookup_expr="iexact",
            label=(
                "The abbreviation of the parent jurisdiction. For example, MA returns "
                "the state's local jurisdictions."
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
            field_name="level", label="Levels: f for federal, s for state, l for local"
        )

        class Meta:
            """List of filters for the API"""

            model = Jurisdiction
            fields = ("abbrev", "level", "name")

    filterset_class = JurisdictionFilter
