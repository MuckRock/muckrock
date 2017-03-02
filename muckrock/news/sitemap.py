"""
Sitemap for News application
"""

from django.contrib.sitemaps import Sitemap

from news_sitemaps import register, NewsSitemap

from muckrock.news.models import Article


class ArticleSitemap(Sitemap):
    """Sitemap for Articles"""

    priority = 0.7
    changefreq = 'never'
    limit = 500

    def items(self):
        """Return all news articles"""
        return Article.objects.get_published()

    def lastmod(self, obj):
        """When was the article last modified?"""
        # pylint: disable=no-self-use
        return obj.pub_date


class ArticleNewsSitemap(NewsSitemap):
    """Article sitemap for Google News"""
    limit = 500

    def items(self):
        """Return all news articles"""
        return Article.objects.get_published().prefetch_related('tags')

    def lastmod(self, obj):
        """When was the article last modified?"""
        # pylint: disable=no-self-use
        return obj.pub_date

    def keywords(self, obj):
        """Keywords for the article"""
        return ','.join(t.name for t in obj.tags.all())

register(articles=ArticleNewsSitemap)
