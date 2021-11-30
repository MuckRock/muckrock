"""
URL mappings for the FOIA application
"""

# Django
from django.urls import re_path
from django.views.generic.base import RedirectView

# MuckRock
from muckrock.core.views import jurisdiction
from muckrock.foia import feeds, views

foia_url = r"(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)"
old_foia_url = r"(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)"

urlpatterns = [
    re_path(r"^$", views.RequestExploreView.as_view(), name="foia-root"),
    # List Views
    re_path(r"^list/$", views.RequestList.as_view(), name="foia-list"),
    re_path(r"^mylist/$", views.MyRequestList.as_view(), name="foia-mylist"),
    re_path(
        r"^organization-list/$", views.MyOrgRequestList.as_view(), name="foia-org-list"
    ),
    re_path(
        r"^proxy-list/$", views.MyProxyRequestList.as_view(), name="foia-proxy-list"
    ),
    re_path(
        r"^agency-list/$", views.AgencyRequestList.as_view(), name="foia-agency-list"
    ),
    re_path(
        r"^list/following/$",
        views.FollowingRequestList.as_view(),
        name="foia-list-following",
    ),
    re_path(
        r"^list/processing/$",
        views.ProcessingRequestList.as_view(),
        name="foia-list-processing",
    ),
    re_path(
        r"^mylist/drafts/$", views.ComposerList.as_view(), name="foia-mylist-drafts"
    ),
    re_path(
        r"^communications/$",
        views.AdminCommunicationView.as_view(),
        name="communication-list",
    ),
    # Create and Draft Views
    re_path(r"^create/$", views.CreateComposer.as_view(), name="foia-create"),
    re_path(
        r"^(?P<idx>\d+)/draft/$", views.UpdateComposer.as_view(), name="foia-draft"
    ),
    re_path(r"^(?P<idx>\d+)/$", RedirectView.as_view(pattern_name="foia-draft")),
    re_path(r"^composer-autosave/(?P<idx>\d+)/$", views.autosave, name="foia-autosave"),
    # Detail View
    re_path(
        r"^%s/$" % foia_url,
        views.Detail.as_view(template_name="foia/detail.html"),
        name="foia-detail",
    ),
    re_path(
        r"^multirequest/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/$",
        views.ComposerDetail.as_view(),
        name="foia-composer-detail",
    ),
    re_path(
        r"^%s/crowdfund/$" % foia_url, views.crowdfund_request, name="foia-crowdfund"
    ),
    re_path(
        r"^%s/files/$" % foia_url, views.FOIAFileListView.as_view(), name="foia-files"
    ),
    re_path(r"^%s/follow/$" % foia_url, views.follow, name="foia-follow"),
    re_path(r"^%s/embargo/$" % foia_url, views.embargo, name="foia-embargo"),
    re_path(
        r"^%s/toggle-followups/$" % foia_url,
        views.toggle_autofollowups,
        name="foia-toggle-followups",
    ),
    # This just redirects to the composer
    re_path(
        r"^multi/(?P<slug>[\w\d_-]+)-(?P<pk>\d+)/$",
        views.MultiDetail.as_view(),
        name="foia-multi-detail",
    ),
    # Misc Views
    re_path(r"^acronyms/$", views.acronyms, name="foia-acronyms"),
    re_path(r"^raw_email/(?P<idx>\d+)/$", views.raw, name="foia-raw"),
    re_path(
        r"^foiarequest-autocomplete/$",
        views.FOIARequestAutocomplete.as_view(),
        name="foia-request-autocomplete",
    ),
    # Feeds
    re_path(
        r"^feeds/submitted/$",
        feeds.LatestSubmittedRequests(),
        name="foia-submitted-feed",
    ),
    re_path(r"^feeds/completed/$", feeds.LatestDoneRequests(), name="foia-done-feed"),
    re_path(r"^feeds/(?P<idx>\d+)/$", feeds.FOIAFeed(), name="foia-feed"),
    re_path(
        r"^feeds/submitted/(?P<username>[\w\-.@ ]+)/$",
        feeds.UserSubmittedFeed(),
        name="foia-user-submitted-feed",
    ),
    re_path(
        r"^feeds/completed/(?P<username>[\w\-.@ ]+)/$",
        feeds.UserDoneFeed(),
        name="foia-user-done-feed",
    ),
    re_path(
        r"^feeds/agency/(?P<idx>\d+)/$",
        feeds.AgencySubmittedFeed(),
        name="foia-agency-feed",
    ),
    re_path(
        r"^feeds/jurisdiction/(?P<idx>\d+)/$",
        feeds.JurisdictionSubmittedFeed(),
        name="foia-jurisdiction-feed",
    ),
    re_path(
        r"^feeds/(?P<username>[\w\-.@ ]+)/$",
        feeds.UserUpdateFeed(),
        name="foia-user-feed",
    ),
    # Files
    re_path(
        r"^file/(?P<pk>\d+)/embed/$", views.FileEmbedView.as_view(), name="file-embed"
    ),
    # Webhooks
    re_path(r"^lob/$", views.lob_webhook, name="lob-webhook"),
    # Old URLS
    re_path(r"^multi/$", RedirectView.as_view(url="/foi/create/")),
    re_path(
        r"^create_multi/$",
        RedirectView.as_view(url="/foi/create/"),
        name="foia-create-multi",
    ),
    re_path(
        r"^mylist/multirequest/$",
        RedirectView.as_view(url="/foi/mylist/"),
        name="foia-mymulti",
    ),
    re_path(
        r"^(?P<jurisdiction>[\w\d_-]+)-(?P<idx>\d+)/$",
        jurisdiction,
        name="foia-jurisdiction",
    ),
    re_path(
        r"^list/user/(?P<user_name>[\w\d_.@ ]+)/$",
        RedirectView.as_view(url="/foi/list/user-%(user_name)s"),
    ),
    re_path(
        r"^list/tag/(?P<tag_slug>[\w\d_.@-]+)/$",
        RedirectView.as_view(url="/foi/list/tag-%(tag_slug)s"),
    ),
    re_path(r"^(?P<action>[\w_-]+)/%s/$" % old_foia_url, views.redirect_old),
    re_path(
        r"^list/user-(?P<user_pk>[\w\d_.@ -]+)/$",
        RedirectView.as_view(url="/foi/list/?user=%(user_pk)s"),
        name="foia-list-user",
    ),
    re_path(
        r"^list/agency-(?P<agency>[\w\d_.@ -]+)-(?P<idx>\d+)/$",
        RedirectView.as_view(url="/foi/list/?agency=%(idx)s"),
        name="foia-list-agency",
    ),
    re_path(
        r"^list/place-(?P<jurisdiction>[\w\d_.@ -]+)-(?P<idx>\d+)/$",
        RedirectView.as_view(url="/foi/list/?jurisdiction=%(idx)s"),
        name="foia-list-jurisdiction",
    ),
    re_path(
        r"^list/tag-(?P<tag_slug>[\w\d_.@-]+)/$",
        RedirectView.as_view(url="/foi/list/?tags=%(tag_slug)s"),
        name="foia-list-tag",
    ),
    re_path(
        r"^list/status-(?P<status>[\w\d_.@ -]+)/$",
        RedirectView.as_view(url="/foi/list/?status=%(status)s"),
        name="foia-list-status",
    ),
    re_path(
        r"^mylist/(?P<view>\w+)/$",
        RedirectView.as_view(url="foi/mylist/"),
        name="foia-mylist-old",
    ),
]
