"""
Sitemap for News application
"""

from django.contrib.sitemaps import Sitemap

from muckrock.news.models import Article

class LimitSitemap(Sitemap):
    """Limit Sitemap"""
    limit = 2000

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
