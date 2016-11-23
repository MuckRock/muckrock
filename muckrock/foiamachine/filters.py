"""
QuerySet filters for FOIA Machine models
"""

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.agency.models import Agency
from muckrock.foiamachine.models import FoiaMachineRequest
from muckrock.jurisdiction.models import Jurisdiction

class FoiaMachineRequestFilter(django_filters.FilterSet):
    """Allows FOIA Machine Requests to be filtered by their status, jurisdiction, or agency."""
    jurisdiction = django_filters.ModelChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.ChoiceWidget('JurisdictionAutocomplete'))
    agency = django_filters.ModelChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.ChoiceWidget('AgencyAutocomplete'))

    class Meta:
        model = FoiaMachineRequest
        fields = ['status', 'jurisdiction', 'agency']
