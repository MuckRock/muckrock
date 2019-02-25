"""
API ViewSets for the accounts application
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import (
    DjangoModelPermissionsOrAnonReadOnly,
    IsAdminUser,
)

# MuckRock
from muckrock.accounts.models import Statistics
from muckrock.accounts.serializers import StatisticsSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """API views for User
    This is used by squarelet to push changes to MuckRock
    """
    queryset = (
        User.objects.order_by('id').prefetch_related('profile', 'groups')
    )
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
    filter_fields = ('username', 'profile__full_name', 'email', 'is_staff')
    lookup_field = 'profile__uuid'

    def update(self, request, *args, **kwargs):
        # uuid in profile is only writable for creates
        if 'profile' in request.data:
            request.data['profile'].pop('uuid', None)
        return super(UserViewSet, self).update(request, *args, **kwargs)


class StatisticsViewSet(viewsets.ModelViewSet):
    """API views for Statistics"""
    queryset = Statistics.objects.all()
    serializer_class = StatisticsSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    filter_fields = ('date',)
