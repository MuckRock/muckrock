"""
Filters for the Q&A app
"""

# Django
from django import forms
from django.contrib.auth.models import User

# Third Party
import django_filters
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.core.filters import RangeWidget
from muckrock.qanda.models import Question
from muckrock.tags.models import Tag


class QuestionFilterSet(django_filters.FilterSet):
    """Allows question to be filtered by user, date, or if it's unanswered."""
    user = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete')
    )
    date = django_filters.DateFromToRangeFilter(
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(
            attrs={
                'class': 'datepicker',
                'placeholder': 'MM/DD/YYYY',
            }
        ),
    )
    unanswered = django_filters.BooleanFilter(
        method='unanswered_filter', widget=forms.CheckboxInput()
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    def unanswered_filter(self, queryset, name, value):
        """Filter to show either only unanswered questions or all questions"""
        # pylint: disable=unused-argument
        if value:
            return queryset.filter(answers__isnull=True)
        else:
            return queryset

    class Meta:
        model = Question
        fields = ['user', 'date']
