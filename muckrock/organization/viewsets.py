"""
API ViewSets for the organization app
"""

# Django
from django.db import transaction
from django.http.response import Http404

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_204_NO_CONTENT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

# MuckRock
from muckrock.organization.models import Membership, Organization
from muckrock.organization.serializers import (
    MembershipReadSerializer,
    MembershipWriteSerializer,
    OrganizationSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    """API views for Organization
    This is used by squarelet to push changes to MuckRock
    """
    queryset = Organization.objects.order_by('id')
    serializer_class = OrganizationSerializer
    permission_classes = (IsAdminUser,)
    filter_fields = ('name', 'private', 'individual', 'plan')
    lookup_field = 'uuid'

    def update(self, request, *args, **kwargs):
        # remove any uuid set in the data - we do not want to override existing uuid
        # it is not set to read only so we can set it on creation
        request.data.pop('uuid', None)
        try:
            response = (
                super(OrganizationViewSet,
                      self).update(request, *args, **kwargs)
            )
        except Http404:
            # allow "updating" a non existing organization in order to create one
            # with the given uuid
            request.data['uuid'] = self.kwargs['uuid']
            response = self.create(request, *args, **kwargs)
        return response


class MembershipViewSet(viewsets.ModelViewSet):
    """API views for Memberships
    This is used by squarelet to push changes to MuckRock
    """
    permission_classes = (IsAdminUser,)
    filter_fields = ('active',)
    lookup_field = 'user__profile__uuid'

    def get_serializer_class(self):
        """Have separate read/write serializers"""
        # we should only be using GET/POST/DELETE
        if self.request.method == "POST":
            return MembershipWriteSerializer
        else:
            return MembershipReadSerializer

    def get_queryset(self):
        """Filter memberships for the chosen organization"""
        return Membership.objects.filter(
            organization__uuid=self.kwargs['organization_uuid']
        ).select_related('user__profile', 'organization').order_by('id')

    def create(self, request, *args, **kwargs):
        request.data['organization'] = kwargs['organization_uuid']
        return super(MembershipViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Checks for individual and active memberships"""
        # pylint: disable=unused-argument
        membership = self.get_object()
        if membership.organization.individual:
            # cannot remove a user from their individual organization
            return Response(
                {
                    'error':
                        'Trying to remove a user from their individual organization'
                },
                status=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        with transaction.atomic():
            if membership.active:
                # if we are deleting the active membership, set the users individual
                # organization to active
                membership.user.memberships.filter(
                    organization__individual=True
                ).update(active=True)
            membership.delete()
        return Response(status=HTTP_204_NO_CONTENT)
