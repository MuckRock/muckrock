"""
Feeds for the FOIA application
"""

# pylint: disable=no-name-in-module
from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import escape, linebreaks

from muckrock.foia.models import FOIARequest, FOIACommunication

class LatestSubmittedRequests(Feed):
    """An RSS Feed for submitted FOIA requests"""
    title = 'Muckrock Submitted Requests'
    link = '/foi/'
    description = 'Recently submitted FOI requests on MuckRock'

    def items(self):
        """Return the items for the rss feed"""
        # pylint: disable=no-self-use
        # pylint: disable=E1103
        return (FOIARequest.objects
                .get_submitted()
                .get_public()
                .order_by('-date_submitted')
                .select_related('jurisdiction')
                .prefetch_related('communications')[:25])

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
        # pylint: disable=no-self-use
        # pylint: disable=E1103
        return (FOIARequest.objects
                .get_done()
                .get_public()
                .order_by('-date_done')
                .select_related('jurisdiction')
                .prefetch_related('communications')[:25])

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request()))


class FOIAFeed(Feed):
    """Feed for an individual FOI request"""
    # pylint: disable=no-self-use

    def get_object(self, request, idx):
        """Get the FOIA Request for this feed"""
        # pylint: disable=arguments-differ
        foia = get_object_or_404(FOIARequest, pk=idx)
        if not foia.is_public():
            raise Http404()
        return foia

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


class UserSubmittedFeed(Feed):
    """Feed for a user's new submitted requests"""
    # pylint: disable=no-self-use

    def get_object(self, request, username):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(User, username=username)

    def title(self, obj):
        """The title of this feed"""
        return 'MuckRock user %s\'s submitted requests' % obj.username

    def link(self, obj):
        """The link for this feed"""
        return obj.profile.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return 'Newly submitted requests by %s' % obj.username

    def items(self, obj):
        """The submitted requests are the items for this feed"""
        return (FOIARequest.objects
                .get_submitted()
                .filter(user=obj, embargo=False)
                .order_by('-date_submitted')
                .select_related('jurisdiction')
                .prefetch_related('communications')[:25])

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request()))


class UserDoneFeed(Feed):
    """Feed for a user's completed requests"""
    # pylint: disable=no-self-use

    def get_object(self, request, username):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(User, username=username)

    def title(self, obj):
        """The title of this feed"""
        return 'MuckRock user %s\'s completed requests' % obj.username

    def link(self, obj):
        """The link for this feed"""
        return obj.profile.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return 'Completed requests by %s' % obj.username

    def items(self, obj):
        """The completed requests are the items for this feed"""
        return (FOIARequest.objects
                .get_done()
                .filter(user=obj, embargo=False)
                .order_by('-date_submitted')
                .select_related('jurisdiction')
                .prefetch_related('communications')[:25])

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request()))


class UserUpdateFeed(Feed):
    """Feed for updates to all of user's requests"""
    # pylint: disable=no-self-use

    def get_object(self, request, username):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(User, username=username)

    def title(self, obj):
        """The title of this feed"""
        return 'MuckRock user %s\'s request updates' % obj.username

    def link(self, obj):
        """The link for this feed"""
        return obj.profile.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return 'All request updates by %s' % obj.username

    def items(self, obj):
        """The communications are the items for this feed"""
        communications = (FOIACommunication.objects
                .filter(foia__user=obj)
                .exclude(foia__status='started')
                .exclude(foia__embargo=True)
                .select_related('foia__jurisdiction')
                .order_by('-date'))
        return communications[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.communication))

