""" API ViewSets for accounts """

# Django
import django_filters
from django.contrib.auth.models import User

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# MuckRock
from muckrock.accounts.serializers import UserSerializer

# pylint: disable=too-few-public-methods
class UserFilter(django_filters.FilterSet):
    """ User filters """
    full_name = django_filters.CharFilter(field_name='profile__full_name', lookup_expr='icontains')
    username = django_filters.CharFilter(lookup_expr='icontains')
    state = django_filters.CharFilter(field_name='profile__state', lookup_expr='icontains')

    class Meta:
        """ Fields """
        model = User
        fields = ['full_name', 'username', 'state']

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

    def list(self, request, *args, **kwargs):
        """Show relevant users based on permissions."""
        if request.user.is_authenticated:
            if request.user.is_staff:
                return super().list(request, *args, **kwargs)  # Staff can see all
            # Non-staff users see their own info and organization members
            queryset = self.get_queryset()  # Get organization members
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response(status=403)  # Forbid unauthenticated users

    filterset_fields = ("username", "profile__full_name", "email", "is_staff")
