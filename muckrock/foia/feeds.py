"""
Feeds for the FOIA application
"""

# Django
from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import escape, linebreaks

# MuckRock
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.jurisdiction.models import Jurisdiction


class LatestSubmittedRequests(Feed):
    """An RSS Feed for submitted FOIA requests"""

    title = "Muckrock Submitted Requests"
    link = "/foi/"
    description = "Recently submitted FOI requests on MuckRock"

    def items(self):
        """Return the items for the rss feed"""
        return (
            FOIARequest.objects.get_public()
            .order_by("-composer__datetime_submitted")
            .select_related("agency__jurisdiction")
            .prefetch_related("communications")[:25]
        )

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request_text()))


class LatestDoneRequests(Feed):
    """An RSS Feed for completed FOIA requests"""

    title = "Muckrock Completed Requests"
    link = "/foi/"
    description = "Recently completed FOI requests on MuckRock"

    def items(self):
        """Return the items for the rss feed"""
        return (
            FOIARequest.objects.get_done()
            .get_public()
            .order_by("-datetime_done")
            .select_related("agency__jurisdiction")
            .prefetch_related("communications")[:25]
        )

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request_text()))


class FOIAFeed(Feed):
    """Feed for an individual FOI request"""

    def get_object(self, request, idx):
        """Get the FOIA Request for this feed"""
        # pylint: disable=arguments-differ
        foia = get_object_or_404(FOIARequest, pk=idx)
        if not foia.is_public():
            raise Http404()
        return foia

    def title(self, obj):
        """The title of this feed"""
        return "MuckRock FOI Request: %s" % obj.title

    def link(self, obj):
        """The link for this feed"""
        return obj.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return "Updates on FOI Request %s from MuckRock" % obj.title

    def items(self, obj):
        """The communications are the items for this feed"""
        return obj.communications.all()[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.communication))


class UserSubmittedFeed(Feed):
    """Feed for a user's new submitted requests"""

    def get_object(self, request, username):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(User, username=username)

    def title(self, obj):
        """The title of this feed"""
        return "MuckRock user %s's submitted requests" % obj.username

    def link(self, obj):
        """The link for this feed"""
        return obj.profile.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return "Newly submitted requests by %s" % obj.username

    def items(self, obj):
        """The submitted requests are the items for this feed"""
        return (
            FOIARequest.objects.filter(composer__user=obj, embargo_status="public")
            .order_by("-composer__datetime_submitted")
            .select_related("agency__jurisdiction")
            .prefetch_related("communications")[:25]
        )

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request_text()))


class UserDoneFeed(Feed):
    """Feed for a user's completed requests"""

    def get_object(self, request, username):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(User, username=username)

    def title(self, obj):
        """The title of this feed"""
        return "MuckRock user %s's completed requests" % obj.username

    def link(self, obj):
        """The link for this feed"""
        return obj.profile.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return "Completed requests by %s" % obj.username

    def items(self, obj):
        """The completed requests are the items for this feed"""
        return (
            FOIARequest.objects.get_done()
            .filter(composer__user=obj, embargo_status="public")
            .order_by("-composer__datetime_submitted")
            .select_related("agency__jurisdiction")
            .prefetch_related("communications")[:25]
        )

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request_text()))


class UserUpdateFeed(Feed):
    """Feed for updates to all of user's requests"""

    def get_object(self, request, username):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(User, username=username)

    def title(self, obj):
        """The title of this feed"""
        return "MuckRock user %s's request updates" % obj.username

    def link(self, obj):
        """The link for this feed"""
        return obj.profile.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return "All request updates by %s" % obj.username

    def items(self, obj):
        """The communications are the items for this feed"""
        communications = (
            FOIACommunication.objects.filter(
                foia__composer__user=obj, foia__embargo_status="public"
            )
            .select_related("foia__agency__jurisdiction")
            .order_by("-datetime")
        )
        return communications[:25]

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.communication))


class AgencySubmittedFeed(Feed):
    """Feed for an agency's new submitted requests"""

    def get_object(self, request, idx):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(Agency, pk=idx)

    def title(self, obj):
        """The title of this feed"""
        return "MuckRock agency %s's submitted requests" % obj.name

    def link(self, obj):
        """The link for this feed"""
        return obj.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return "Newly submitted requests for %s" % obj.name

    def items(self, obj):
        """The submitted requests are the items for this feed"""
        return (
            FOIARequest.objects.filter(agency=obj, embargo_status="public")
            .order_by("-composer__datetime_submitted")
            .select_related("agency__jurisdiction")
            .prefetch_related("communications")[:25]
        )

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request_text()))


class JurisdictionSubmittedFeed(Feed):
    """Feed for an agency's new submitted requests"""

    def get_object(self, request, idx):
        """Get the user for this feed"""
        # pylint: disable=arguments-differ
        return get_object_or_404(Jurisdiction, pk=idx)

    def title(self, obj):
        """The title of this feed"""
        return "MuckRock jurisdiction %s's submitted requests" % obj.name

    def link(self, obj):
        """The link for this feed"""
        return obj.get_absolute_url()

    def description(self, obj):
        """The description of this feed"""
        return "Newly submitted requests for %s" % obj.name

    def items(self, obj):
        """The submitted requests are the items for this feed"""
        return (
            FOIARequest.objects.filter(
                agency__jurisdiction=obj, embargo_status="public"
            )
            .order_by("-composer__datetime_submitted")
            .select_related("agency__jurisdiction")
            .prefetch_related("communications")[:25]
        )

    def item_description(self, item):
        """The description of each rss item"""
        return linebreaks(escape(item.first_request_text()))
