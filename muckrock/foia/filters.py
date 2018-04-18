"""
Filters for FOIA models
"""

# Django
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q

# Standard Library
import re

# Third Party
import django_filters
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.agency.models import Agency
from muckrock.filters import BLANK_STATUS, NULL_BOOLEAN_CHOICES, RangeWidget
from muckrock.foia.models import FOIAComposer, FOIARequest
from muckrock.foia.models.composer import STATUS as COMPOSER_STATUS
from muckrock.project.models import Project
from muckrock.tags.models import Tag


class JurisdictionFilterSet(django_filters.FilterSet):
    """Mix in for including state inclusive jurisdiction filter"""
    jurisdiction = django_filters.CharFilter(
        widget=autocomplete_light.
        MultipleChoiceWidget('JurisdictionStateInclusiveAutocomplete'),
        method='filter_jurisdiction',
        label='Jurisdiction',
    )
    value_format = re.compile(r'\d+-(True|False)')
    jurisdiction_field = 'jurisdiction'

    def filter_jurisdiction(self, queryset, name, value):
        """Filter jurisdction, allowing for state inclusive searches"""
        #pylint: disable=unused-argument
        values = self.request.GET.getlist('jurisdiction')
        query = Q()
        for value in values:
            if not self.value_format.match(value):
                continue
            pk, include_local = value.split('-')
            include_local = include_local == 'True'
            query |= Q(**{'{}__pk'.format(self.jurisdiction_field): pk})
            if include_local:
                query |= Q(
                    **{
                        '{}__parent__pk'.format(self.jurisdiction_field): pk
                    }
                )
        return queryset.filter(query)


class FOIARequestFilterSet(JurisdictionFilterSet):
    """Allows filtering a request by status, agency, jurisdiction, user, or tags."""
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    user = django_filters.ModelMultipleChoiceFilter(
        name='composer__user',
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.MultipleChoiceWidget('AgencyAutocomplete')
    )
    projects = django_filters.ModelMultipleChoiceFilter(
        name='projects',
        queryset=lambda request: Project.objects.get_visible(request.user),
        widget=autocomplete_light.MultipleChoiceWidget('ProjectAutocomplete'),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
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
        widget=RangeWidget(
            attrs={
                'class': 'datepicker',
                'placeholder': 'MM/DD/YYYY',
            }
        ),
    )

    class Meta:
        model = FOIARequest
        fields = ['status', 'user', 'agency', 'jurisdiction', 'projects']


class MyFOIARequestFilterSet(JurisdictionFilterSet):
    """Allows filtering a request by status, agency, jurisdiction, or tags."""
    status = django_filters.ChoiceFilter(choices=BLANK_STATUS)
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.MultipleChoiceWidget('AgencyAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
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
        widget=RangeWidget(
            attrs={
                'class': 'datepicker',
                'placeholder': 'MM/DD/YYYY',
            }
        ),
    )

    class Meta:
        model = FOIARequest
        fields = ['status', 'agency', 'jurisdiction']


class ProcessingFOIARequestFilterSet(JurisdictionFilterSet):
    """Allows filtering a request by user, agency, jurisdiction, or tags."""
    user = django_filters.ModelMultipleChoiceFilter(
        name='composer__user',
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
    agency = django_filters.ModelMultipleChoiceFilter(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.MultipleChoiceWidget('AgencyAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = FOIARequest
        fields = ['user', 'agency', 'jurisdiction']


class AgencyFOIARequestFilterSet(django_filters.FilterSet):
    """Filters for agency users"""
    user = django_filters.ModelMultipleChoiceFilter(
        name='composer__user',
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )
    date_range = django_filters.DateFromToRangeFilter(
        name='communications__date',
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(
            attrs={
                'class': 'datepicker',
                'placeholder': 'MM/DD/YYYY',
            }
        ),
    )

    class Meta:
        model = FOIARequest
        fields = ['user']


class ComposerFilterSet(django_filters.FilterSet):
    """Filters for composers"""
    status = django_filters.ChoiceFilter(choices=COMPOSER_STATUS)

    class Meta:
        model = FOIAComposer
        fields = ['status']
