"""
API ViewSets for the accounts application
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, IsAdminUser

# MuckRock
from muckrock.accounts.models import Statistics
from muckrock.accounts.serializers import StatisticsSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """API views for User
    This is used by squarelet to push changes to MuckRock
    """

    # remove UserViewSet - it is not used by squarelet anymore
    queryset = User.objects.order_by("id").prefetch_related("profile", "groups")
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
    filterset_fields = ("username", "profile__full_name", "email", "is_staff")


class StatisticsViewSet(viewsets.ModelViewSet):
    """API views for Statistics"""

    queryset = Statistics.objects.all()
    serializer_class = StatisticsSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    filterset_fields = ("date",)
