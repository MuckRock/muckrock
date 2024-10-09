"""
Provides Jurisdiction application API views
"""

# Standard Library
import logging

# Third Party
import django_filters
from rest_framework.viewsets import ModelViewSet
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.jurisdiction.serializers import JurisdictionSerializer

class JurisdictionViewSet(viewsets.ReadOnlyModelViewSet):
    """API views for Jurisdiction"""

    queryset = Jurisdiction.objects.order_by("id").select_related("parent__parent")
    serializer_class = JurisdictionSerializer
    ordering_fields = [
        f
        for f in JurisdictionSerializer.Meta.fields
        if f
        not in ("absolute_url", "average_response_time", "fee_rate", "success_rate")
    ]

    class JurisdictionFilter(django_filters.FilterSet):
        """API Filters for Jurisdictions"""

        parent = django_filters.NumberFilter(field_name="parent__id")

        class Meta:
            model = Jurisdiction
            fields = ("name", "abbrev", "level", "parent")

    def get_queryset(self):
        """Custom queryset to filter by name, abbrev, and level.
           Allows you to fuzzy search: spring will return Springfield"""
        queryset = super().get_queryset()

        name = self.request.query_params.get('name', None)
        abbrev = self.request.query_params.get('abbrev', None)
        level = self.request.query_params.get('level', None)

        if name:
            queryset = queryset.filter(name__icontains=name)

        if abbrev:
            queryset = queryset.filter(abbrev__iexact=abbrev)

        if level:
            queryset = queryset.filter(level=level)

        return queryset
