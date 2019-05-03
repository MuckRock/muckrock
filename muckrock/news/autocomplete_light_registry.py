"""
Autocomplete registry for news articles
"""

# Django
from django.contrib.auth.models import User
from django.db.models.query import Prefetch

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.news.models import Article


class ArticleAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Creates an autocomplete for picking articles"""
    choices = Article.objects.get_published().prefetch_related(
        Prefetch('authors', User.objects.select_related('profile'))
    ).distinct()
    choice_template = 'autocomplete/article.html'
    search_fields = ['title', 'tags__name']
    attrs = {
        'placeholder': 'Search for articles',
        'data-autocomplete-minimum-characters': 1
    }


autocomplete_light.register(Article, ArticleAutocomplete)
