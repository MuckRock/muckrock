""" API ViewSets for accounts """

# Django
from django.contrib.auth.models import User

# Third Party
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

# MuckRock
from muckrock.accounts.api_v2.serializers import StatisticsSerializer, UserSerializer
from muckrock.accounts.models import Statistics
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
    uuid = django_filters.CharFilter(
        field_name="profile__uuid",
        lookup_expr="icontains",
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

    queryset = User.objects.order_by("id").prefetch_related("profile")
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    filterset_class = UserFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()  # Staff can see all users
        # Non-staff users see members of their organization
        return User.objects.filter(
            organizations__in=user.organizations.all()
        ).distinct()

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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["date"]
