"""
Provides Jurisdiction application API views
"""

from django.db.models import Q

from rest_framework.decorators import list_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from muckrock.jurisdiction.models import Jurisdiction, Exemption
from muckrock.jurisdiction.serializers import JurisdictionSerializer, ExemptionSerializer

class JurisdictionViewSet(ModelViewSet):
    """API views for Jurisdiction"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Jurisdiction.objects.select_related('parent__parent').order_by()
    serializer_class = JurisdictionSerializer
    filter_fields = ('name', 'abbrev', 'level', 'parent')


class ExemptionViewSet(ModelViewSet):
    """
    The Exemption model provides a list of individual exemption cases along with some
    example appeal language.

    Search exemptions with the API at the `/exemption/search/` endpoint.
    """
    queryset = (Exemption.objects.select_related('jurisdiction__parent__parent')
                                 .prefetch_related('example_appeals'))
    serializer_class = ExemptionSerializer
    filter_fields = ('name', 'jurisdiction')

    @list_route()
    def search(self, request):
        """
        Allow searches against the collection of exemptions.
        Jurisdiction is an optional filter.
        """
        query = request.query_params.get('q')
        jurisdiction = request.query_params.get('jurisdiction')
        if query is None:
            raise ValidationError({'Error': 'Must provide a query'})
        results = self.queryset.filter(
            Q(name__icontains=query)|
            Q(basis__icontains=query)|
            Q(example_appeals__language__icontains=query)|
            Q(tags__name__icontains=query)
        ).distinct()
        if jurisdiction:
            results = results.filter(jurisdiction__pk=jurisdiction)
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)
