"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from pingback import register_pingback

# pylint: disable=W0611
import foia.signals
# pylint: enable=W0611
from foia import views
from foia.feeds import LatestSubmittedRequests, LatestDoneRequests
from foia.pingbacks import pingback_foia_handler
from muckrock.views import jurisdiction

foia_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<idx>\d+)-(?P<slug>[\w\d_-]+)'
old_foia_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

register_pingback(views.detail, pingback_foia_handler)

urlpatterns = patterns('',
    url(r'^$',                             redirect_to, {'url': 'list'}, name='foia-root'),
    url(r'^list/$',                        views.list_, name='foia-list'),
    url(r'^list/user-(?P<user_name>[\w\d_.@i]+)/$',
                                           views.list_by_user, name='foia-list-user'),
    url(r'^list/tag-(?P<tag_slug>[\w\d_.@-]+)/$',
                                           views.list_by_tag, name='foia-list-tag'),
    url(r'^list/following/$',              views.list_following, name='foia-list-following'),
    url(r'^mylist/$',                      views.my_list, name='foia-mylist-all'),
    url(r'^mylist/(?P<view>\w+)/$',        views.my_list, name='foia-mylist'),

    url(r'^new/$',                         views.create, name='foia-create'),
    url(r'^doc_cloud/(?P<doc_id>[\w\d_-]+)/$',
                                           views.doc_cloud_detail, name='foia-doc-cloud-detail'),
    url(r'^(?P<jurisdiction>[\w\d_-]+)/$', jurisdiction, name='foia-jurisdiction'),
    url(r'^%s/$' % foia_url,               redirect_to, {'url': 'view'}, name='foia-default'),
    url(r'^%s/view/$' % foia_url,          views.detail, name='foia-detail'),
    url(r'^%s/update/$' % foia_url,        views.update, name='foia-update'),
    url(r'^%s/fix/$' % foia_url,           views.fix, name='foia-fix'),
    url(r'^%s/admin-fix/$' % foia_url,     views.admin_fix, name='foia-admin-fix'),
    url(r'^%s/appeal/$' % foia_url,        views.appeal, name='foia-appeal'),
    url(r'^%s/flag/$' % foia_url,          views.flag, name='foia-flag'),
    url(r'^%s/add_note/$' % foia_url,      views.note, name='foia-note'),
    url(r'^%s/delete/$' % foia_url,        views.delete, name='foia-delete'),
    url(r'^%s/embargo/$' % foia_url,       views.embargo, name='foia-embargo'),
    url(r'^%s/pay/$' % foia_url,           views.pay_request, name='foia-pay'),
    url(r'^%s/follow/$' % foia_url,        views.follow, name='foia-follow'),
    url(r'^feeds/submitted/$',             LatestSubmittedRequests(), name='foia-submitted-feed'),
    url(r'^feeds/completed/$',             LatestDoneRequests(), name='foia-done-feed'),

    # old patterns for redirects
    url(r'^list/user/(?P<user_name>[\w\d_.@i]+)/$',
                                           redirect_to, {'url': '/foi/list/user-%(user_name)s'}),
    url(r'^list/tag/(?P<tag_slug>[\w\d_.@-]+)/$',
                                           redirect_to, {'url': '/foi/list/tag-%(tag_slug)s'}),
)

# old patterns for redirects
# pylint: disable=W0142
actions = ('view', 'update', 'fix', 'admin-fix', 'appeal',
           'add_notes', 'delete', 'embargo', 'pay', 'follow')
urlpatterns += patterns('',
    *(url(r'^%s/%s/$' % (action, old_foia_url), redirect_to,
          {'url': '/foi/%%(jurisdiction)s/%%(idx)s-%%(slug)s/%s/' % action})
      for action in actions))
