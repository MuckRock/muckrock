"""
Filters for the Agency application
"""

# Third Party
import django_filters
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core import autocomplete
from muckrock.jurisdiction.models import Jurisdiction


class AgencyFilterSet(django_filters.FilterSet):
    """Allows agencies to be filtered by jurisdiction."""

    jurisdiction = django_filters.ModelChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Search for jurisdiction"},
        ),
    )

    class Meta:
        model = Agency
        fields = ["jurisdiction"]
