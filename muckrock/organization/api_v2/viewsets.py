"""
API ViewSets for organizations
"""

# Third Party
import django_filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# MuckRock
from muckrock.core.pagination import APIV2CursorPagination
from muckrock.core.views import AuthenticatedAPIMixin
from muckrock.organization.api_v2.serializers import OrganizationSerializer
from muckrock.organization.models import Organization


class OrganizationFilter(django_filters.FilterSet):
    """Organization filters"""

    name = django_filters.CharFilter(
        lookup_expr="icontains", label="The name of the organization."
    )
    slug = django_filters.CharFilter(
        lookup_expr="icontains", label="The slug (URL identifier) for the organization."
    )
    uuid = django_filters.CharFilter(
        lookup_expr="icontains", label="The unique identifier for the organization."
    )

    class Meta:
        """Fields"""

        model = Organization
        fields = ["name", "slug", "uuid"]


class OrganizationViewSet(AuthenticatedAPIMixin, viewsets.ReadOnlyModelViewSet):
    """API views for organizations"""

    queryset = Organization.objects.prefetch_related("users")
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = OrganizationFilter
    pagination_class = APIV2CursorPagination

    def get_queryset(self):
        """Staff see all organizations, others see only their own"""
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(users=self.request.user)
