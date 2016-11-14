"""
Filters for the project application
"""

from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
import django_filters

from muckrock.project.models import Project
from muckrock.tags.models import Tag

class ProjectFilterSet(django_filters.FilterSet):
    """Allows a project to be filtered by whether it's featured or by its user."""
    contributors = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = Project
        fields = ['contributors', 'tags']
