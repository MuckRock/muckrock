"""
Filters for the news application
"""

from django.contrib.auth.models import User
from django.db.models import Count
import django_filters

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.news.models import Article
from muckrock.tags.models import Tag

class RangeWidget(django_filters.widgets.RangeWidget):
    """Customizes the rendered output of the RangeWidget"""
    def format_output(self, rendered_widgets):
        return ("""
            <div class="input-range">
                <div class="small labels nomargin">
                    <label>Start</label>
                    <label>End</label>
                </div>
                <div class="inputs">
                    %(inputs)s
                </div>
            </div>
        """ % {'inputs': '\n'.join(rendered_widgets)})


class ArticleFilterSet(django_filters.FilterSet):
    """Allows a list of news items to be filtered by a date range, an author, or many tags."""
    authors = django_filters.ModelChoiceFilter(
        queryset=(User.objects.annotate(article_count=Count('authored_articles'))
            .filter(article_count__gt=0)),
        widget=autocomplete_light.ChoiceWidget('UserAuthorAutocomplete')
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
        widget=autocomplete_light.MultipleChoiceWidget('TagAutocomplete'),
    )

    class Meta:
        model = Article
        fields = ['authors', 'pub_date', 'tags']


class ArticleAuthorFilterSet(django_filters.FilterSet):
    """Allows a list of articles by an author to be filtered by a date range or many tags."""
    class Meta:
        model = Article
        fields = ['pub_date', 'tags']
