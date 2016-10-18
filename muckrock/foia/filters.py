"""
Filters for FOIA models
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, STATUS
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.tags.models import Tag

BLANK_STATUS = [('', 'All')] + STATUS

class FOIARequestFilterSet(django_filters.FilterSet):
    """Allows filtering a request by status, agency, jurisdiction, user, or tags."""
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    user = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete')
    )
    agency = django_filters.ModelChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.ChoiceWidget('AgencyAutocomplete')
    )
    jurisdiction = django_filters.ModelChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.ChoiceWidget('JurisdictionAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = FOIARequest
        fields = ['status', 'user', 'agency', 'jurisdiction', 'tags']



class MyFOIARequestFilterSet(django_filters.FilterSet):
    """Allows filtering a request by status, agency, jurisdiction, or tags."""
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    agency = django_filters.ModelChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.ChoiceWidget('AgencyAutocomplete')
    )
    jurisdiction = django_filters.ModelChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.ChoiceWidget('JurisdictionAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = FOIARequest
        fields = ['status', 'agency', 'jurisdiction', 'tags']
