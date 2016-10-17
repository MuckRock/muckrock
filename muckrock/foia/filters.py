"""
Filters for FOIA models
"""

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import Jurisdiction

class FOIARequestFilterSet(django_filters.FilterSet):
    """Allows filtering a request by status, agency, jurisdiction, user, or tags."""
    jurisdiction = django_filters.ModelChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.ChoiceWidget('JurisdictionAutocomplete'))
    agency = django_filters.ModelChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.ChoiceWidget('AgencyAutocomplete'))

    class Meta:
        model = FOIARequest
        fields = ['user', 'status', 'agency', 'jurisdiction', 'tags']
