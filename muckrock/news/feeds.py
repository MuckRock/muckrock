"""
Feeds for the News application
"""

# pylint: disable=E0611
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import escape, linebreaks

from muckrock.news.models import Article

class LatestEntries(Feed):
    """An RSS Feed for news articles"""
    title = 'Muckrock News'
    link = '/news/'
    description = 'The latest news from MuckRock'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable=R0201
        return Article.objects.get_published().order_by('-pub_date')[:5]

    def item_description(self, item):
        """The description of each rss item"""
        # pylint: disable=R0201
        return linebreaks(escape(item.summary))

