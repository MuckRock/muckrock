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

    check_number = django_filters.NumberFilter(
        field_name="number", label="Check #", widget=forms.NumberInput()
    )

    mr_number = django_filters.NumberFilter(
        field_name="communication__foia__pk", label="MR #", widget=forms.NumberInput()
    )

    date_range = django_filters.DateFromToRangeFilter(
        field_name="created_datetime",
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )

    minimum_amount = django_filters.NumberFilter(
        field_name="amount",
        lookup_expr="gte",
        label="Min. Amount",
        widget=forms.NumberInput(),
    )

    outstanding = django_filters.BooleanFilter(
        label="Outstanding",
        widget=forms.Select(choices=NULL_BOOLEAN_CHOICES),
        method="filter_outstanding",
    )

    def filter_outstanding(self, queryset, name, value):
        """Outstanding checks"""
        # pylint: disable=unused-argument
        if value is None:
            return queryset
        elif value:
            return queryset.filter(deposit_date=None)
        else:
            return queryset.exclude(deposit_date=None)

    class Meta:
        model = Check
        fields = [
            "check_number",
            "mr_number",
            "date_range",
            "outstanding",
            "minimum_amount",
        ]
