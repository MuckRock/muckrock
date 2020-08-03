"""
Filters for FOIA models
"""

# Django
from django import forms
from django.contrib.auth.models import User

# Third Party
import django_filters

# MuckRock
from muckrock.core import autocomplete
from muckrock.core.filters import NULL_BOOLEAN_CHOICES
from muckrock.crowdsource.models import Crowdsource


class CrowdsourceFilterSet(django_filters.FilterSet):
    """Filtering for crowdsources for admins"""

    status = django_filters.ChoiceFilter(
        choices=(("draft", "Draft"), ("open", "Open"), ("close", "Closed"))
    )
    is_staff = django_filters.BooleanFilter(
        name="user__is_staff",
        label="Staff Owned",
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
    )
    user = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete", attrs={"data-placeholder": "Search users"}
        ),
    )

    class Meta:
        model = Crowdsource
        fields = ["status", "user"]
