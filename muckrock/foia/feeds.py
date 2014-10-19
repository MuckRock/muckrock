"""
Feeds for the FOIA application
"""

# pylint: disable=E0611
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
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
        return FOIARequest.objects.get_submitted().get_public().order_by('-date_submitted')[:25]

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
        return FOIARequest.objects.get_done().get_public().order_by('-date_done')[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request()))


class FOIAFeed(Feed):
    """Feed for an individual FOI request"""
    # pylint: disable=no-self-use

    def get_object(self, request, idx):
        """Get the FOIA Request for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(FOIARequest, pk=idx)

    def title(self, obj):
        """The title of this feed"""
        return 'MuckRock FOI Request: %s' % obj.title

    def link(self, obj):
        """The link for this feed"""
        return obj.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return 'Updates on FOI Request %s from MuckRock' % obj.title

    def items(self, obj):
        """The communications are the items for this feed"""
        return obj.communications.all()[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.communication))
