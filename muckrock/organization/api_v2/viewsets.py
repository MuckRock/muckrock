"""
API ViewSets for organizations
"""

# Third Party
import django_filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# MuckRock
from muckrock.organization.api_v2.serializers import OrganizationSerializer
from muckrock.organization.models import Organization


class OrganizationFilter(django_filters.FilterSet):
    """Organization filters"""

    name = django_filters.CharFilter(lookup_expr="icontains")
    slug = django_filters.CharFilter(lookup_expr="icontains")
    uuid = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        """Fields"""

        model = Organization
        fields = ["name", "slug", "uuid"]


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
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
