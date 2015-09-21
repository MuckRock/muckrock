"""
URL mappings for the FOIA application
"""

from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView


import muckrock.foia.signals # pylint: disable=unused-import
from muckrock.foia import views
from muckrock.foia.feeds import LatestSubmittedRequests, LatestDoneRequests, FOIAFeed,\
                                UserSubmittedFeed, UserDoneFeed, UserUpdateFeed
from muckrock.views import jurisdiction

# pylint: disable=no-value-for-parameter
# pylint: disable=bad-whitespace
# pylint: disable=bad-continuation

foia_url = r'(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)'
old_foia_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns(
    '',
    # Redirects
    url(r'^$',
        RedirectView.as_view(url='list'), name='foia-root'),
    url(r'^multi/$',
        RedirectView.as_view(url='/foia/create_multi')),

    # List Views
    url(r'^list/$',
        views.RequestList.as_view(),
        name='foia-list'),
    url(r'^mylist/$',
        views.MyRequestList.as_view(),
        name='foia-mylist'),
    url(r'^list/following/$',
        views.FollowingRequestList.as_view(),
        name='foia-list-following'),

    # Create and Draft Views
    url(r'^create/$',
        views.create_request, name='foia-create'),
    url(r'^%s/draft/$' % foia_url,
        views.draft_request, name='foia-draft'),
    url(r'^create_multi/$',
        views.create_multirequest, name='foia-create-multi'),
    url(r'^multi/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/draft/$',
        views.draft_multirequest, name='foia-multi-draft'),

    # Detail View
    url(r'^%s/$' % foia_url,
        views.Detail.as_view(template_name='foia/detail.html'),
        name='foia-detail'),

    url(r'^%s/clone/$' % foia_url,
        views.clone_request, name='foia-clone'),
    url(r'^%s/admin_fix/$' % foia_url,
        views.admin_fix, name='foia-admin-fix'),
    url(r'^%s/add_note/$' % foia_url,
        views.note, name='foia-note'),
    url(r'^%s/delete/$' % foia_url,
        views.delete, name='foia-delete'),
    url(r'^%s/embargo/$' % foia_url,
        views.embargo, name='foia-embargo'),
    url(r'^%s/pay/$' % foia_url,
        views.pay_request, name='foia-pay'),
    url(r'^%s/crowdfund/$' % foia_url,
        views.crowdfund_request, name='foia-crowdfund'),
    url(r'^%s/follow/$' % foia_url,
        views.follow, name='foia-follow'),
    url(r'^%s/toggle-followups/$' % foia_url,
        views.toggle_autofollowups, name='foia-toggle-followups'),

    # Misc Views
    url(r'^(?P<jurisdiction>[\w\d_-]+)-(?P<idx>\d+)/$',
        jurisdiction, name='foia-jurisdiction'),
    url(r'^orphans/$',
        views.orphans, name='foia-orphans'),
    url(r'^acronyms/$',
        views.acronyms, name='foia-acronyms'),
    url(r'^drag_drop/$',
        views.drag_drop, name='foia-drag-drop'),
    url(r'^raw_email/(?P<idx>\d+)/$',
        views.raw, name='foia-raw'),

    # Feeds
    url(r'^feeds/submitted/$',
        LatestSubmittedRequests(), name='foia-submitted-feed'),
    url(r'^feeds/completed/$',
        LatestDoneRequests(), name='foia-done-feed'),
    url(r'^feeds/(?P<idx>\d+)/$',
        FOIAFeed(), name='foia-feed'),
    url(r'^feeds/submitted/(?P<username>[\w\d_.@ ]+)/$',
       UserSubmittedFeed(), name='foia-user-submitted-feed'),
    url(r'^feeds/completed/(?P<username>[\w\d_.@ ]+)/$',
       UserDoneFeed(), name='foia-user-done-feed'),
    url(r'^feeds/(?P<username>[\w\d_.@ ]+)/$',
       UserUpdateFeed(), name='foia-user-feed'),

    # Old URLS
    url(r'^list/user/(?P<user_name>[\w\d_.@ ]+)/$',
        RedirectView.as_view(url='/foi/list/user-%(user_name)s')),
    url(r'^list/tag/(?P<tag_slug>[\w\d_.@-]+)/$',
        RedirectView.as_view(url='/foi/list/tag-%(tag_slug)s')),
    url(r'^(?P<action>[\w_-]+)/%s/$' % old_foia_url,
        views.redirect_old),
    url(r'^list/user-(?P<user_pk>[\w\d_.@ -]+)/$',
        RedirectView.as_view(url='/foi/list/?user=%(user_pk)s'),
        name='foia-list-user'),
    url(r'^list/agency-(?P<agency>[\w\d_.@ -]+)-(?P<idx>\d+)/$',
        RedirectView.as_view(url='/foi/list/?agency=%(idx)s'),
        name='foia-list-agency'),
    url(r'^list/place-(?P<jurisdiction>[\w\d_.@ -]+)-(?P<idx>\d+)/$',
        RedirectView.as_view(url='/foi/list/?jurisdiction=%(idx)s'),
        name='foia-list-jurisdiction'),
    url(r'^list/tag-(?P<tag_slug>[\w\d_.@-]+)/$',
        RedirectView.as_view(url='/foi/list/?tags=%(tag_slug)s'),
        name='foia-list-tag'),
    url(r'^list/status-(?P<status>[\w\d_.@ -]+)/$',
        RedirectView.as_view(url='/foi/list/?status=%(status)s'),
        name='foia-list-status'),
    url(r'^mylist/(?P<view>\w+)/$',
        RedirectView.as_view(url='foi/mylist/'),
        name='foia-mylist-old'),
)
