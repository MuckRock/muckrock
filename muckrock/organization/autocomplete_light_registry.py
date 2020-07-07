"""
Autocomplete registry for Organizations
"""

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.organization.models import Organization

autocomplete_light.register(
    Organization,
    name="OrganizationAutocomplete",
    choices=Organization.objects.all(),
    search_fields=("name",),
    attrs={
        "placeholder": "Search for organizations",
        "data-autocomplete-minimum-characters": 1,
    },
)
