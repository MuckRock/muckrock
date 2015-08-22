"""
Search Index for the news application
"""

from celery_haystack.indexes import CelerySearchIndex
from haystack.indexes import CharField, DateTimeField, Indexable

from muckrock.news.models import Article

class ArticleIndex(CelerySearchIndex, Indexable):
    """Search index for news articles"""
    text = CharField(document=True, use_template=True)
    #authors = CharField(model_attr='authors')
    pub_date = DateTimeField(model_attr='pub_date')

    def get_model(self):
        """Return model for index"""
        return Article

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        # pylint: disable=no-self-use
        return Article.objects.get_published()


