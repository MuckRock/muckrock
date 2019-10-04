"""Filters for communication app"""

# Django
from django import forms

# Third Party
import django_filters

# MuckRock
from muckrock.communication.models import Check
from muckrock.core.filters import NULL_BOOLEAN_CHOICES, RangeWidget


class CheckFilterSet(django_filters.FilterSet):
    """Filtering for checks"""

    date_range = django_filters.DateFromToRangeFilter(
        name='created_datetime',
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(
            attrs={
                'class': 'datepicker',
                'placeholder': 'MM/DD/YYYY',
            }
        ),
    )

    minimum_amount = django_filters.NumberFilter(
        name='amount',
        lookup_expr='gte',
        label='Min. Amount',
        widget=forms.NumberInput(),
    )

    outstanding = django_filters.BooleanFilter(
        label='Outstanding',
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
        method='filter_outstanding',
    )

    def filter_outstanding(self, queryset, name, value):
        """Outstanding checks"""
        #pylint: disable=unused-argument
        if value is None:
            return queryset
        elif value:
            return queryset.filter(deposit_time=None)
        else:
            return queryset.exclude(deposit_time=None)

    class Meta:
        model = Check
        fields = ['date_range', 'outstanding']
