"""
Viewsets for the Crowdsource application API
"""

# Django
from django.db.models import Prefetch

# Third Party
from django_filters import rest_framework as django_filters
from rest_framework import permissions, viewsets

# MuckRock
from muckrock.crowdsource.models import CrowdsourceResponse, CrowdsourceValue
from muckrock.crowdsource.serializers import CrowdsourceResponseSerializer


class CrowdsourceResponsePermissions(permissions.BasePermission):
    """
    Object-level permission to allow access only to owners of a crowdsource or staff
    """

    def has_object_permission(self, request, view, obj):
        """Is owner or staff?"""
        if request.user.is_staff:
            return True
        return request.user == obj.crowdsource.user


class CrowdsourceResponseViewSet(viewsets.ModelViewSet):
    """API views for CrowdsourceResponse"""
    queryset = (
        CrowdsourceResponse.objects.select_related(
            'crowdsource',
            'data',
            'user',
        ).prefetch_related(
            Prefetch(
                'values',
                queryset=CrowdsourceValue.objects.select_related('field')
                .order_by('field__order')
            )
        ).order_by('id')
    )
    serializer_class = CrowdsourceResponseSerializer
    permission_classes = (CrowdsourceResponsePermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for Crowdsource Responses"""
        crowdsource = django_filters.NumberFilter(name='crowdsource__id')

        class Meta:
            model = CrowdsourceResponse
            fields = ('flag',)

    filter_class = Filter
    search_fields = ('values__value',)
