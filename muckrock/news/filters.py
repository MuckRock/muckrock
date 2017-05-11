"""
Filters for the news application
"""

from django.contrib.auth.models import User
from django.db.models import Count
import django_filters

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.filters import RangeWidget
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.tags.models import Tag

class ArticleFilterSet(django_filters.FilterSet):
    """Allows filtering a list of news articles by author or tags"""
    projects = django_filters.ModelMultipleChoiceFilter(
        name="projects",
        queryset=Project.objects.get_public(),
        widget=autocomplete_light.MultipleChoiceWidget('ProjectAutocomplete'),
    )
    authors = django_filters.ModelMultipleChoiceFilter(
        queryset=(User.objects.annotate(article_count=Count('authored_articles'))
            .filter(article_count__gt=0)),
        widget=autocomplete_light.MultipleChoiceWidget('UserAuthorAutocomplete')
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = Article
        fields = ['projects', 'authors', 'projects']


class ArticleDateRangeFilterSet(django_filters.FilterSet):
    """Allows a list of news items to be filtered by a date range, an author, or many tags."""
    projects = django_filters.ModelMultipleChoiceFilter(
        name="projects",
        queryset=Project.objects.get_public(),
        widget=autocomplete_light.MultipleChoiceWidget('ProjectAutocomplete'),
    )
    authors = django_filters.ModelMultipleChoiceFilter(
        queryset=(User.objects.annotate(article_count=Count('authored_articles'))
            .filter(article_count__gt=0)),
        widget=autocomplete_light.MultipleChoiceWidget('UserAuthorAutocomplete')
    )
    pub_date = django_filters.DateFromToRangeFilter(
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(attrs={
            'class': 'datepicker',
            'placeholder': 'MM/DD/YYYY',
        }),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = Article
        fields = ['projects', 'authors', 'pub_date']


class ArticleAuthorFilterSet(django_filters.FilterSet):
    """Allows a list of articles by an author to be filtered by a date range or many tags."""
    pub_date = django_filters.DateFromToRangeFilter(
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(attrs={
            'class': 'datepicker',
            'placeholder': 'MM/DD/YYYY',
        }),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        name='tags__name',
        queryset=Tag.objects.all(),
        label='Tags',
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = Article
        fields = ['pub_date']
