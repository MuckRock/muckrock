"""
Filters for jurisdiction Views
"""

# Third Party
import django_filters
from dal import forward

# MuckRock
from muckrock.core import autocomplete
from muckrock.jurisdiction.models import Exemption, Jurisdiction

LEVELS = (("", "All"), ("f", "Federal"), ("s", "State"), ("l", "Local"))


class JurisdictionFilterSet(django_filters.FilterSet):
    """Allows jurisdiction to be filtered by level of government and state."""

    level = django_filters.ChoiceFilter(choices=LEVELS)
    parent = django_filters.ModelChoiceFilter(
        label="State",
        queryset=Jurisdiction.objects.filter(level="s", hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Search for state"},
            forward=(forward.Const(["s"], "levels"),),
        ),
    )

    class Meta:
        model = Jurisdiction
        fields = ["level", "parent"]


class ExemptionFilterSet(django_filters.FilterSet):
    """Allows exemptions to be filtered by jurisdiction"""

    jurisdiction = django_filters.ModelChoiceFilter(
        label="Jurisdiction",
        queryset=Jurisdiction.objects.filter(level__in=("s", "f"), hidden=False),
        widget=autocomplete.ModelSelect2Multiple(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Search for jurisdiction"},
            forward=(forward.Const(["s", "f"], "levels"),),
        ),
    )

    class Meta:
        model = Exemption
        fields = ["jurisdiction"]
