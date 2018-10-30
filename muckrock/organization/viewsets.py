"""
API ViewSets for the organization app
"""

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

# MuckRock
from muckrock.organization.models import Organization
from muckrock.organization.serializers import OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    """API views for Organization
    This is used by squarelet to push changes to MuckRock
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAdminUser,)
    filter_fields = ('name', 'private', 'individual', 'plan')
    lookup_field = 'uuid'
