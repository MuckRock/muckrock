"""Filters for communication app"""

# Django
from django import forms

# Third Party
import django_filters

# MuckRock
from muckrock.communication.models import CHECK_STATUS, Check
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

    status = django_filters.ChoiceFilter(choices=CHECK_STATUS)

    class Meta:
        model = Check
        fields = ["check_number", "mr_number", "date_range", "status", "minimum_amount"]
