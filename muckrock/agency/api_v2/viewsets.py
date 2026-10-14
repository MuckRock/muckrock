"""Viewsets for Agency"""

# Django
from django.db.models import Q

# Third Party
import django_filters
from rest_framework import filters, viewsets

# MuckRock
from muckrock.agency.api_v2.serializers import AgencySerializer
from muckrock.agency.models import Agency
from muckrock.core.pagination import APIV2CursorPagination
from muckrock.core.views import AuthenticatedAPIMixin
from muckrock.jurisdiction.models import Jurisdiction


# pylint: disable=too-few-public-methods
class AgencyFilter(django_filters.FilterSet):
    """API Filter for Agencies"""

    jurisdiction__id = django_filters.NumberFilter(
        field_name="jurisdiction__id", label="Jurisdiction ID"
    )
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Agency Name"
    )
    type = django_filters.CharFilter(
        field_name="types__name", lookup_expr="iexact", label="Agency Type"
    )
    state = django_filters.NumberFilter(
        method="filter_state",
        label="State ID",
        help_text="ID of a state jurisdiction; matches state agencies and local agencies within it",
    )

    def filter_state(self, queryset, name, value):
        """Agencies in the given state, at the state or local level"""
        jurisdictions = Jurisdiction.objects.filter(
            Q(pk=value, level="s") | Q(parent_id=value, level="l")
        ).values("pk")
        return queryset.filter(jurisdiction__in=jurisdictions)

    class Meta:
        """Filters"""

        model = Agency
        fields = ("name", "jurisdiction__id", "state", "type")


# pylint: disable=too-few-public-methods, too-many-ancestors
class AgencyViewSet(AuthenticatedAPIMixin, viewsets.ReadOnlyModelViewSet):
    """API views for Agency"""

    serializer_class = AgencySerializer
    pagination_class = APIV2CursorPagination
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        filters.SearchFilter,
    ]
    search_fields = [
        "name",
    ]
    filterset_class = AgencyFilter

    def get_queryset(self):
        """Filter out non-approved agencies for non-staff"""
        qs = Agency.objects.select_related("jurisdiction").prefetch_related("types")
        if not self.request.user.is_staff:
            qs = qs.filter(status="approved")
        return qs
