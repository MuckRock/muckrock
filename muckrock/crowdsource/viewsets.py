"""
Viewsets for the Crowdsource application API
"""

# Django
from django.db.models import Q

# Third Party
from django_filters import rest_framework as django_filters
from rest_framework import mixins, permissions, viewsets

# MuckRock
from muckrock.crowdsource.models import Crowdsource, CrowdsourceResponse
from muckrock.crowdsource.serializers import (
    CrowdsourceResponseAdminSerializer,
    CrowdsourceResponseGallerySerializer,
)


class Permissions(permissions.DjangoObjectPermissions):
    """Use Django Object permissions as the base for our assignment permissions"""

    def has_permission(self, request, view):
        """Authenticated users permissions will be checked on a per object basis
        Return true here to continue to the object check
        Anonymous users have read-only access
        """
        if request.user.is_authenticated:
            return True
        else:
            return request.method in permissions.SAFE_METHODS


class CrowdsourceResponseViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """API views for CrowdsourceResponse"""

    queryset = (
        CrowdsourceResponse.objects.select_related(
            "crowdsource", "data", "user__profile", "edit_user__profile",
        )
        .prefetch_related("crowdsource__fields", "values", "tags",)
        .order_by("id")
    )
    permission_classes = (Permissions,)

    def get_serializer_class(self):
        """Get the serializer class"""
        if self.request.user.is_staff:
            return CrowdsourceResponseAdminSerializer
        try:
            crowdsource = Crowdsource.objects.get(
                pk=self.request.GET.get("crowdsource")
            )
        except Crowdsource.DoesNotExist:
            return CrowdsourceResponseGallerySerializer

        if self.request.user.has_perm("crowdsource.change_crowdsource", crowdsource):
            return CrowdsourceResponseAdminSerializer
        else:
            return CrowdsourceResponseGallerySerializer

    def get_queryset(self):
        """Filter the queryset"""
        if self.request.user.is_staff:
            return self.queryset
        elif self.request.user.is_authenticated:
            return self.queryset.filter(
                Q(crowdsource__user=self.request.user)
                | Q(
                    crowdsource__project_admin=True,
                    crowdsource__project__contributors=self.request.user,
                )
                | Q(gallery=True)
            ).distinct()
        else:
            return self.queryset.filter(gallery=True)

    class Filter(django_filters.FilterSet):
        """API Filter for Crowdsource Responses"""

        crowdsource = django_filters.NumberFilter(name="crowdsource__id")

        class Meta:
            model = CrowdsourceResponse
            fields = (
                "id",
                "flag",
            )

    filter_class = Filter
    search_fields = (
        "values__value",
        "tags__name",
    )
