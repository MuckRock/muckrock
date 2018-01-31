"""
Feeds for the QandA application
"""

# Django
# pylint: disable=no-name-in-module
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import escape, linebreaks

# MuckRock
from muckrock.qanda.models import Question


class LatestQuestions(Feed):
    """An RSS Feed for Questions"""
    title = 'MuckRock Questions'
    link = '/questions/'
    description = 'Latest community questions about FOI topics on MuckRock'

    def items(self):
        """Return the items for the rss feed"""
        return Question.objects.all().order_by('-date')[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.question))
