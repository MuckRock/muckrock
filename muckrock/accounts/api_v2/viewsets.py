""" API ViewSets for accounts """

# Django
import django_filters
from django.contrib.auth.models import User

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# MuckRock
from muckrock.accounts.api_v2.serializers import UserSerializer

# pylint: disable=too-few-public-methods
class UserFilter(django_filters.FilterSet):
    """ User filters """
    full_name = django_filters.CharFilter(field_name='profile__full_name', lookup_expr='icontains')
    username = django_filters.CharFilter(lookup_expr='icontains')
    uuid = django_filters.CharFilter(field_name='profile__uuid', lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        """ Fields """
        model = User
        fields = ['full_name', 'username', 'uuid', 'email']

class UserViewSet(viewsets.ModelViewSet):
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
        return User.objects.filter(organizations__in=user.organizations.all()).distinct()

    def get_object(self):
        """Allow one to lookup themselves by specifying `me` as the pk."""
        if self.kwargs["pk"] == "me" and self.request.user.is_authenticated:
            return self.request.user  # Return the current user
        return super().get_object()
