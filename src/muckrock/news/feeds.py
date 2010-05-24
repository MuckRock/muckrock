"""
Feeds for the News application
"""

# pylint: disable-msg=E0611
from django.contrib.syndication.views import Feed
from news.models import Article

class LatestEntries(Feed):
    """An RSS Feed for news articles"""
    title = 'Latest News'
    link = '/news/'
    description = 'Updates on changes and additions to News on MuckRock.com'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable-msg=R0201
        return Article.objects.get_published().order_by('-pub_date')[:5]

    def item_description(self, item):
        """The description of each rss item"""
        # pylint: disable-msg=R0201
        return item.summary

