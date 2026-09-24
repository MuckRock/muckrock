"""API ViewSets for accounts"""

# Django
from django.contrib.auth.models import User

# Third Party
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated

# MuckRock
from muckrock.accounts.api_v2.serializers import StatisticsSerializer, UserSerializer
from muckrock.accounts.models import Statistics
from muckrock.core.pagination import APIV2CursorPagination
from muckrock.core.views import AuthenticatedAPIMixin


# pylint: disable=too-few-public-methods
class UserFilter(django_filters.FilterSet):
    """User filters"""

    full_name = django_filters.CharFilter(
        field_name="profile__full_name",
        lookup_expr="icontains",
        label="The full name of the user.",
    )
    username = django_filters.CharFilter(
        lookup_expr="icontains", label="The unique username of the user."
    )
    uuid = django_filters.UUIDFilter(
        field_name="profile__uuid",
        label="The unique identifier (UUID) of the user's profile.",
    )
    email = django_filters.CharFilter(
        lookup_expr="icontains", label="The email address of the user."
    )

    id = django_filters.NumberFilter(label="The ID of the user")

    class Meta:
        """Fields"""

        model = User
        fields = ["id", "full_name", "username", "uuid", "email"]


class UserViewSet(AuthenticatedAPIMixin, viewsets.ReadOnlyModelViewSet):
    """API views for users"""

    queryset = User.objects.select_related("profile").prefetch_related("organizations")
    serializer_class = UserSerializer
    # The mixin will set this permission class to IsAuthenticated when
    # settings.API_V2_AUTH is set, but this sets it to IsAuthenticated
    # even if this isn't set, which is the old behavior.
    permission_classes = (IsAuthenticated,)
    filterset_class = UserFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = APIV2CursorPagination

    def get_queryset(self):
        """Staff can see all users.
        Non-staff can only see users they share an org membership with.
        """
        user = self.request.user
        queryset = super().get_queryset()
        if user.is_staff:
            return queryset
        return queryset.filter(organizations__in=user.organizations.all()).distinct()

    def get_object(self):
        """Allow one to lookup themselves by specifying `me` as the pk."""
        if self.kwargs["pk"] == "me" and self.request.user.is_authenticated:
            return self.request.user  # Return the current user
        return super().get_object()


class StatisticsViewSet(AuthenticatedAPIMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Statistics.
    Restricted to admin users only.
    """

    queryset = Statistics.objects.all()
    serializer_class = StatisticsSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {"date": ["exact", "gte", "lte"]}
    ordering_fields = ["date"]
    ordering = ["-date"]
    pagination_class = APIV2CursorPagination
