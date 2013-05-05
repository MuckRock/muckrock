"""
Search Index for the news application
"""

from haystack.indexes import SearchIndex, CharField, DateTimeField
from haystack import site

from muckrock.news.models import Article

class ArticleIndex(SearchIndex):
    """Search index for news articles"""
    text = CharField(document=True, use_template=True)
    authors = CharField(model_attr='authors')
    pub_date = DateTimeField(model_attr='pub_date')

    def get_queryset(self):
        """Used when the entire index for model is updated."""
        # pylint: disable=R0201
        return Article.objects.get_published()

site.register(Article, ArticleIndex)
