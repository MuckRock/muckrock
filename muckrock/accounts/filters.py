"""
Filters for accounts
"""

# Third Party
import django_filters
from dal import forward

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.core import autocomplete
from muckrock.jurisdiction.models import Jurisdiction


class ProxyFilterSet(django_filters.FilterSet):
    """Allows proxies to be filtered by location."""

    location = django_filters.ModelMultipleChoiceFilter(
        label="State",
        queryset=Jurisdiction.objects.filter(level="s", hidden=False),
        widget=autocomplete.ModelSelect2Multiple(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Search for state"},
            forward=(forward.Const(["s"], "levels"),),
        ),
    )

    class Meta:
        model = Profile
        fields = ["location"]
