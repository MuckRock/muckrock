"""
Autocomplete registry for news articles
"""

from muckrock.news.models import Article

from autocomplete_light import shortcuts as autocomplete_light

autocomplete_light.register(
    Article,
    name='ArticleAutocomplete',
    choices=Article.objects.get_published(),
    search_fields=('title',),
    attrs={
        'placeholder': 'Search for articles',
        'data-autocomplete-minimum-characters': 1})
