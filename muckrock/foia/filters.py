"""
Filters for FOIA models
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.agency.models import Agency
from muckrock.filters import RangeWidget
from muckrock.foia.models import FOIARequest, FOIAMultiRequest, STATUS
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.project.models import Project
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
    date_range = django_filters.DateFromToRangeFilter(
        name='communications__date',
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(attrs={
            'class': 'datepicker',
            'placeholder': 'MM/DD/YYYY',
        }),
    )
    projects = django_filters.ModelMultipleChoiceFilter(
        name="projects",
        queryset=Project.objects.get_public(),
        widget=autocomplete_light.MultipleChoiceWidget('ProjectAutocomplete'),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = FOIARequest
        fields = ['status', 'user', 'agency', 'jurisdiction', 'projects', 'tags']



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


class MyFOIAMultiRequestFilterSet(django_filters.FilterSet):
    """Allows multirequests to be filtered by status."""
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS[:3])

    class Meta:
        model = FOIAMultiRequest
        fields = ['status']


class ProcessingFOIARequestFilterSet(django_filters.FilterSet):
    """Allows filtering a request by user, agency, jurisdiction, or tags."""
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
        fields = ['user', 'agency', 'jurisdiction', 'tags']
