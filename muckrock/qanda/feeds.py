"""
Feeds for the QandA application
"""

# pylint: disable=E0611
from django.contrib.syndication.views import Feed

from muckrock.qanda.models import Question

class LatestQuestions(Feed):
    """An RSS Feed for Questions"""
    title = 'Latest FOIA Questions'
    link = '/questions/'
    description = 'Latest questions about FOI topics on MuckRock.com'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable=R0201
        # pylint: disable=E1103
        return Question.objects.all().order_by('-date')[:5]

    def item_description(self, item):
        """The description of each rss item"""
        return item.question

