"""
API ViewSets for organizations
"""

# Third Party
import django_filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# MuckRock
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


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet, AuthenticatedAPIMixin):
    """API views for organizations"""

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = OrganizationFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Organization.objects.all()  # Staff can see all organizations
        # Non-staff users see only organizations they are members of
        return Organization.objects.filter(users=user)
