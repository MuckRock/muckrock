"""
Sitemap for News application
"""

from django.contrib.sitemaps import Sitemap

from news_sitemaps import register, NewsSitemap

from muckrock.news.models import Article

class LimitSitemap(Sitemap):
    """Limit Sitemap"""
    limit = 500

class ArticleSitemap(LimitSitemap):
    """Sitemap for Articles"""

    priority = 0.7
    changefreq = 'never'

    def items(self):
        """Return all news articles"""
        return Article.objects.get_published()

    def lastmod(self, obj):
        """When was the article last modified?"""
        # pylint: disable=R0201
        return obj.pub_date

class ArticleNewsSitemap(NewsSitemap):
    """Article sitemap for Google News"""
    limit = 5000

    def items(self):
        """Return all news articles"""
        return Article.objects.get_published()

    def lastmod(self, obj):
        """When was the article last modified?"""
        # pylint: disable=R0201
        return obj.pub_date

register(articles=ArticleNewsSitemap)
