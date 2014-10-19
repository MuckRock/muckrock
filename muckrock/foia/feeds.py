"""
Feeds for the FOIA application
"""

# pylint: disable=E0611
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import escape, linebreaks

from muckrock.foia.models import FOIARequest

class LatestSubmittedRequests(Feed):
    """An RSS Feed for submitted FOIA requests"""
    title = 'Muckrock Submitted Requests'
    link = '/foi/'
    description = 'Recently submitted FOI requests on MuckRock'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable=R0201
        # pylint: disable=E1103
        return FOIARequest.objects.get_submitted().get_public().order_by('-date_submitted')[:5]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request()))

class LatestDoneRequests(Feed):
    """An RSS Feed for completed FOIA requests"""
    title = 'Muckrock Completed Requests'
    link = '/foi/'
    description = 'Recently completed FOI requests on MuckRock'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable=R0201
        # pylint: disable=E1103
        return FOIARequest.objects.get_done().get_public().order_by('-date_done')[:5]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request()))
