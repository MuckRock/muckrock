"""
Feeds for the News application
"""

# Django
# pylint: disable=no-name-in-module
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import escape, linebreaks

# MuckRock
from muckrock.news.models import Article


class LatestEntries(Feed):
    """An RSS Feed for news articles"""
    title = 'Muckrock News'
    link = '/news/'
    description = 'The latest news from MuckRock'

    def items(self):
        """Return the items for the rss feed"""
        return Article.objects.get_published().order_by('-pub_date')[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.summary))
