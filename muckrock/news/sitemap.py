"""
Sitemap for News application
"""

# Django
from django.contrib.sitemaps import Sitemap
from django.utils import timezone

# Standard Library
from datetime import timedelta

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


class ArticleNewsSitemap(Sitemap):
    """Google News sitemap of articles from the last two days"""

    limit = 500

    def items(self):
        """Return recently published news articles"""
        return Article.objects.get_published().filter(
            pub_date__gte=(timezone.now() - timedelta(2))
        )

    def lastmod(self, obj):
        """When was the article published, to the second?"""
        return obj.pub_date.replace(microsecond=0)
