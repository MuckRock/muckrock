"""
Sitemap for News application
"""

# Django
from django.contrib.sitemaps import Sitemap
from django.utils import timezone

# Standard Library
from datetime import timedelta

# Third Party
from news_sitemaps import register
from news_sitemaps.sitemaps import NewsSitemap

# MuckRock
from muckrock.news.models import Article


class ArticleSitemap(Sitemap):
    """Sitemap for Articles"""

    priority = 0.7
    changefreq = "never"
    limit = 500

    def items(self):
        """Return all news articles"""
        return Article.objects.get_published()

    def lastmod(self, obj):
        """When was the article last modified?"""
        return obj.pub_date


class ArticleNewsSitemap(NewsSitemap):
    """Article sitemap for Google News"""

    limit = 500

    def items(self):
        """Return all news articles"""
        return (
            Article.objects.get_published()
            .filter(pub_date__gte=(timezone.now() - timedelta(2)))
            .prefetch_related("tags")
        )

    def lastmod(self, obj):
        """When was the article last modified?"""
        return obj.pub_date

    def keywords(self, obj):
        """Keywords for the article"""
        return ",".join(t.name for t in obj.tags.all())


register(articles=ArticleNewsSitemap)
