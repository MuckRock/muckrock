"""
Filters for the task application
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.task.models import (
    Task,
    ResponseTask,
)

class TaskFilterSet(django_filters.FilterSet):
    """Allows tasks to be filtered by whether they're resolved, and by who resolved them."""
    resolved = django_filters.BooleanFilter(
        label='Show Resolved',
        widget=forms.CheckboxInput())
    resolved_by = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserTaskAutocomplete')
    )

    class Meta:
        model = Task
        fields = ['resolved', 'resolved_by']

class ResponseTaskFilterSet(TaskFilterSet):
    class Meta:
        model = ResponseTask
        fields = ['predicted_status', 'resolved', 'resolved_by']
