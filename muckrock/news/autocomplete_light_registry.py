"""
Autocomplete registry for news articles
"""

from muckrock.news.models import Article

from autocomplete_light import shortcuts as autocomplete_light

class ArticleAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Creates an autocomplete for picking articles"""
    choices = Article.objects.get_published()
    choice_template = 'autocomplete/article.html'
    search_fields = ['title']
    attrs = {
        'placeholder': 'Search for articles',
        'data-autocomplete-minimum-characters': 1
    }

autocomplete_light.register(Article, ArticleAutocomplete)
