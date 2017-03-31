"""
Filters for FOIA models
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.agency.models import Agency
from muckrock.filters import RangeWidget, BLANK_STATUS, NULL_BOOLEAN_CHOICES
from muckrock.foia.models import FOIARequest, FOIAMultiRequest
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.project.models import Project
from muckrock.tags.models import Tag


class FOIARequestFilterSet(django_filters.FilterSet):
    """Allows filtering a request by status, agency, jurisdiction, user, or tags."""
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    user = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.MultipleChoiceWidget('AgencyAutocomplete')
    )
    jurisdiction = django_filters.ModelMultipleChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.MultipleChoiceWidget('JurisdictionAutocomplete')
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
    has_embargo = django_filters.BooleanFilter(
        name='embargo',
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
    )
    has_crowdfund = django_filters.BooleanFilter(
        name='crowdfund',
        lookup_expr='isnull',
        exclude=True,
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
    )
    minimum_pages = django_filters.NumberFilter(
        name='communications__files__pages',
        lookup_expr='gte',
        label='Min. Pages',
        distinct=True,
        widget=forms.NumberInput(),
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


    class Meta:
        model = FOIARequest
        fields = ['status', 'user', 'agency', 'jurisdiction', 'projects', 'tags']


class MyFOIARequestFilterSet(django_filters.FilterSet):
    """Allows filtering a request by status, agency, jurisdiction, or tags."""
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.MultipleChoiceWidget('AgencyAutocomplete')
    )
    jurisdiction = django_filters.ModelMultipleChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.MultipleChoiceWidget('JurisdictionAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )
    has_embargo = django_filters.BooleanFilter(
        name='embargo',
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
    )
    has_crowdfund = django_filters.BooleanFilter(
        name='crowdfund',
        lookup_expr='isnull',
        exclude=True,
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
    )
    minimum_pages = django_filters.NumberFilter(
        name='communications__files__pages',
        lookup_expr='gte',
        label='Min. Pages',
        distinct=True,
        widget=forms.NumberInput(),
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
    user = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.MultipleChoiceWidget('AgencyAutocomplete')
    )
    jurisdiction = django_filters.ModelMultipleChoiceFilter(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete_light.MultipleChoiceWidget('JurisdictionAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = FOIARequest
        fields = ['user', 'agency', 'jurisdiction', 'tags']


class AgencyFOIARequestFilterSet(django_filters.FilterSet):
    """Filters for agency users"""
    user = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
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


    class Meta:
        model = FOIARequest
        fields = ['user', 'tags']
