"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.base import RedirectView

from pingback import register_pingback

# pylint: disable=W0611
import muckrock.foia.signals
# pylint: enable=W0611
from muckrock.crowdfund import views as crowdfund_views
from muckrock.foia import views
from muckrock.foia.feeds import LatestSubmittedRequests, LatestDoneRequests
from muckrock.foia.pingbacks import pingback_foia_handler
from muckrock.views import jurisdiction

# pylint: disable=E1120

foia_url = r'(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)'
old_foia_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

register_pingback(views.Detail.as_view(), pingback_foia_handler)

urlpatterns = patterns('',
    url(r'^$',                             RedirectView.as_view(url='list'), name='foia-root'),
    url(r'^list/$',                        views.List.as_view(), name='foia-list'),
    url(r'^list/user-(?P<user_name>[\w\d_.@ -]+)/$',
                                           views.ListByUser.as_view(), name='foia-list-user'),
    url(r'^list/agency-(?P<agency>[\w\d_.@ -]+)-(?P<idx>\d+)/$',
                                           views.ListByAgency.as_view(), name='foia-list-agency'),
    url(r'^list/place-(?P<jurisdiction>[\w\d_.@ -]+)-(?P<idx>\d+)/$',
                                           views.ListByJurisdiction.as_view(),
                                           name='foia-list-jurisdiction'),
    url(r'^list/tag-(?P<tag_slug>[\w\d_.@-]+)/$',
                                           views.ListByTag.as_view(), name='foia-list-tag'),
    url(r'^list/following/$',              views.ListFollowing.as_view(),
                                           name='foia-list-following'),
    url(r'^mylist/$',                      views.MyList.as_view(), name='foia-mylist-all'),
    url(r'^mylist/(?P<view>\w+)/$',        views.MyList.as_view(), name='foia-mylist'),

    url(r'^new/$',                         views.create, name='foia-create'),
    url(r'^(?P<jurisdiction>[\w\d_-]+)-(?P<idx>\d+)/$',
                                           jurisdiction, name='foia-jurisdiction'),
    url(r'^multi/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/update/$',
                                           views.multirequest_update, name='foia-multi-update'),
    url(r'^multi/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)/$',
                                           views.multiple, name='foia-multi'),
    url(r'^multi/$',                       RedirectView.as_view(url='/foia/new')),
    url(r'^%s/$' % foia_url,               views.Detail.as_view(), name='foia-detail'),
    url(r'^%s/update/$' % foia_url,        views.update, name='foia-update'),
    url(r'^%s/admin_fix/$' % foia_url,     views.admin_fix, name='foia-admin-fix'),
    url(r'^%s/add_note/$' % foia_url,      views.note, name='foia-note'),
    url(r'^%s/delete/$' % foia_url,        views.delete, name='foia-delete'),
    url(r'^%s/embargo/$' % foia_url,       views.embargo, name='foia-embargo'),
    url(r'^%s/pay/$' % foia_url,           views.pay_request, name='foia-pay'),
    url(r'^%s/crowdfund/$' % foia_url,     views.crowdfund_request, name='foia-crowdfund'),
    url(r'^%s/contribute/$' % foia_url,    crowdfund_views.contribute_request,
                                               name='foia-contribute'),
    url(r'^%s/follow/$' % foia_url,        views.follow, name='foia-follow'),
    url(r'^feeds/submitted/$',             LatestSubmittedRequests(), name='foia-submitted-feed'),
    url(r'^feeds/completed/$',             LatestDoneRequests(), name='foia-done-feed'),

    # old patterns for redirects
    url(r'^list/user/(?P<user_name>[\w\d_.@ ]+)/$',
                                          RedirectView.as_view(url='/foi/list/user-%(user_name)s')),
    url(r'^list/tag/(?P<tag_slug>[\w\d_.@-]+)/$',
                                          RedirectView.as_view(url='/foi/list/tag-%(tag_slug)s')),
    url(r'^(?P<action>[\w_-]+)/%s/$' % old_foia_url,
                                          views.redirect_old), 
)

