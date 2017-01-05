"""
Filters for the Q&A app
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.filters import RangeWidget
from muckrock.qanda.models import Question


class QuestionFilterSet(django_filters.FilterSet):
    """Allows question to be filtered by user, date, or if it's unanswered."""
    user = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete')
    )
    date = django_filters.DateFromToRangeFilter(
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(attrs={
            'class': 'datepicker',
            'placeholder': 'MM/DD/YYYY',
        }),
    )
    unanswered = django_filters.MethodFilter(
        action='unanswered_filter',
        widget=forms.CheckboxInput()
    )

    def unanswered_filter(self, queryset, value):
        """Filter to show either only unanswered questions or all questions"""
        # pylint: disable=no-self-user
        if value:
            return queryset.filter(answers__isnull=True)
        else:
            return queryset

    class Meta:
        model = Question
        fields = ['user', 'date']
