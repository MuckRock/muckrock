"""
Filters for the task application
"""

from django import forms
from django.contrib.auth.models import User
from django.db.models import Count

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.filters import RangeWidget
from muckrock.task.models import Task

class TaskFilterSet(django_filters.FilterSet):
    """Allows tasks to be filtered by whether they're resolved, and by who resolved them."""
    resolved = django_filters.BooleanFilter(widget=forms.CheckboxInput())
    resolved_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserTaskAutocomplete')
    )

    class Meta:
        model = Task
        fields = ['resolved', 'resolved_by']
