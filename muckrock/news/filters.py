"""
Filters for the news application
"""

from django.contrib.auth.models import User
import django_filters

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.news.models import Article


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
    """Allows a list of news items to be filtered by date or author."""
    authors = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget('UserAutocomplete')
    )
    pub_date = django_filters.DateFromToRangeFilter(
        label='Date Range',
        lookup_expr='contains',
        widget=RangeWidget(attrs={
            'class': 'datepicker',
            'placeholder': 'MM/DD/YYYY',
        }),
    )

    class Meta:
        model = Article
        fields = ['authors', 'pub_date']
