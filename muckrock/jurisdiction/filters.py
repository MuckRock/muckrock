"""
Filters for jurisdiction Views
"""

# Third Party
import django_filters
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.jurisdiction.models import Exemption, Jurisdiction

LEVELS = (('', 'All'), ('f', 'Federal'), ('s', 'State'), ('l', 'Local'))


class JurisdictionFilterSet(django_filters.FilterSet):
    """Allows jurisdiction to be filtered by level of government and state."""
    level = django_filters.ChoiceFilter(choices=LEVELS)
    parent = django_filters.ModelChoiceFilter(
        label='State',
        queryset=Jurisdiction.objects.filter(level='s', hidden=False),
        widget=autocomplete_light.ChoiceWidget('StateAutocomplete')
    )

    class Meta:
        model = Jurisdiction
        fields = ['level', 'parent']


class ExemptionFilterSet(django_filters.FilterSet):
    """Allows exemptions to be filtered by jurisdiction"""
    jurisdiction = django_filters.ModelChoiceFilter(
        label='Jurisdiction',
        queryset=Jurisdiction.objects.filter(
            level__in=('s', 'f'),
            hidden=False,
        ),
        widget=autocomplete_light.ChoiceWidget('FederalStateAutocomplete')
    )

    class Meta:
        model = Exemption
        fields = ['jurisdiction']
