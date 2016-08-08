from rest_framework import viewsets

from muckrock.jurisdiction.models import Jurisdiction, Exemption
from muckrock.jurisdiction.serializers import JurisdictionSerializer, ExemptionSerializer

class JurisdictionViewSet(viewsets.ModelViewSet):
    """API views for Jurisdiction"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Jurisdiction.objects.select_related('parent__parent').order_by()
    serializer_class = JurisdictionSerializer
    filter_fields = ('name', 'abbrev', 'level', 'parent')


class ExemptionViewSet(viewsets.ModelViewSet):
    """API views for Exemption"""
    queryset = (Exemption.objects.select_related('jurisdiction__parent__parent')
                                 .prefetch_related('example_appeals'))
    serializer_class = ExemptionSerializer
    filter_fields = ('name', 'jurisdiction')

