"""
QuerySet filters for FOIA Machine models
"""

# Third Party
import django_filters
from autocomplete_light import shortcuts as autocomplete_light
from dal import autocomplete

# MuckRock
from muckrock.agency.models import Agency
from muckrock.foiamachine.models import FoiaMachineRequest
from muckrock.jurisdiction.models import Jurisdiction


class FoiaMachineRequestFilter(django_filters.FilterSet):
    """Allows FOIA Machine Requests to be filtered by their status, jurisdiction, or agency."""

    jurisdiction = django_filters.ModelChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.ChoiceWidget("JurisdictionAutocomplete"),
    )
    agency = django_filters.ModelChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            attrs={
                "data-placeholder": "Search agencies",
                "data-minimum-input-length": 0,
                "data-html": True,
                "data-dropdown-css-class": "select2-dropdown",
                "data-width": "100%",
            },
        ),
    )

    class Meta:
        model = FoiaMachineRequest
        fields = ["status", "jurisdiction", "agency"]
