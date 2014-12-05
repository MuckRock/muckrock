"""
Feeds for the QandA application
"""

# pylint: disable=E0611
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import escape, linebreaks

from muckrock.qanda.models import Question

class LatestQuestions(Feed):
    """An RSS Feed for Questions"""
    title = 'MuckRock Questions'
    link = '/questions/'
    description = 'Latest community questions about FOI topics on MuckRock'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable=R0201
        # pylint: disable=E1103
        return Question.objects.all().order_by('-date')[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.question))

