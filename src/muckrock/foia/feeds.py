"""
Feeds for the FOIA application
"""

# pylint: disable-msg=E0611
from django.contrib.syndication.views import Feed

from foia.models import FOIARequest

class LatestSubmittedRequests(Feed):
    """An RSS Feed for submitted FOIA requests"""
    title = 'Latest Submitted Requests'
    link = '/foi/'
    description = 'Updates on changes and additions to submitted FOIA Requests on MuckRock.com'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable-msg=R0201
        # pylint: disable-msg=E1103
        return FOIARequest.objects.get_submitted().get_public().order_by('-date_submitted')[:5]

    def item_description(self, item):
        """The description of each rss item"""
        return item.first_request()

class LatestDoneRequests(Feed):
    """An RSS Feed for completed FOIA requests"""
    title = 'Latest Completed Requests'
    link = '/foi/'
    description = 'Updates on changes and additions to completed FOIA Requests on MuckRock.com'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable-msg=R0201
        # pylint: disable-msg=E1103
        return FOIARequest.objects.get_done().get_public().order_by('-date_done')[:5]

    def item_description(self, item):
        """The description of each rss item"""
        return item.first_request()
