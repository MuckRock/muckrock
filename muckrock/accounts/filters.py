"""
Filters for accounts
"""

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.accounts.models import Profile
from muckrock.jurisdiction.models import Jurisdiction

class ProxyFilterSet(django_filters.FilterSet):
    """Allows proxies to be filtered by location."""
    location = django_filters.ModelMultipleChoiceFilter(
        label='State',
        queryset=Jurisdiction.objects.filter(level='s', hidden=False),
        widget=autocomplete_light.MultipleChoiceWidget('StateAutocomplete')
    )

    class Meta:
        model = Profile
        fields = ['location']
