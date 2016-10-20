"""
Filters for the news application
"""

from django.contrib.auth.models import User
import django_filters

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.news.models import Article

class ArticleFilterSet(django_filters.FilterSet):
    """Allows a list of news items to be filtered by date or author."""
    authors = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete')
    )

    class Meta:
        model = Article
        fields = ['authors', 'pub_date']
