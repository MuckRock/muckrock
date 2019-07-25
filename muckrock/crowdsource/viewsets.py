"""
Viewsets for the Crowdsource application API
"""

# Django
from django.db.models import Q

# Third Party
from django_filters import rest_framework as django_filters
from rest_framework import permissions, viewsets

# MuckRock
from muckrock.crowdsource.models import CrowdsourceResponse
from muckrock.crowdsource.serializers import CrowdsourceResponseSerializer


class CrowdsourceResponsePermissions(permissions.BasePermission):
    """
    Object-level permission to allow access only to owners of a crowdsource or staff
    """

    def has_object_permission(self, request, view, obj):
        """Is owner or staff?"""
        return request.user.has_perm(
            'crowdsource.view_crowdsource', obj.crowdsource
        )


class CrowdsourceResponseViewSet(viewsets.ModelViewSet):
    """API views for CrowdsourceResponse"""
    queryset = (
        CrowdsourceResponse.objects.select_related(
            'crowdsource',
            'data',
            'user__profile',
            'edit_user__profile',
        ).prefetch_related(
            'crowdsource__fields',
            'values',
            'tags',
        ).order_by('id')
    )
    serializer_class = CrowdsourceResponseSerializer
    permission_classes = (CrowdsourceResponsePermissions,)

    def get_queryset(self):
        """Filter the queryset"""
        if self.request.user.is_staff:
            return self.queryset
        elif self.request.user.is_authenticated:
            return self.queryset.filter(
                Q(crowdsource__user=self.request.user) | Q(
                    crowdsource__project_admin=True,
                    crowdsource__project__contributors=self.request.user,
                )
            )
        else:
            return self.queryset.none()

    class Filter(django_filters.FilterSet):
        """API Filter for Crowdsource Responses"""
        crowdsource = django_filters.NumberFilter(name='crowdsource__id')

        class Meta:
            model = CrowdsourceResponse
            fields = (
                'id',
                'flag',
            )

    filter_class = Filter
    search_fields = (
        'values__value',
        'tags__name',
    )
