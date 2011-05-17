"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns, url

from pingback import register_pingback

# pylint: disable-msg=W0611
import foia.signals
# pylint: enable-msg=W0611
from foia import views
from foia.feeds import LatestSubmittedRequests, LatestDoneRequests
from foia.pingbacks import pingback_foia_handler

# change in signals also if this changes (avoid circular imports)
foia_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

register_pingback(views.detail, pingback_foia_handler)

urlpatterns = patterns('',
    url(r'^list/$',                   views.list_, name='foia-list'),
    url(r'^list/user/(?P<user_name>[\w\d_.@]+)/$',
                                      views.list_by_user, name='foia-list-user'),
    url(r'^mylist/(?P<view>\w+)/$',   views.my_list, name='foia-mylist'),
    url(r'^new/$',                    views.create, name='foia-create'),
    url(r'^view/%s/$' % foia_url,     views.detail, name='foia-detail'),
    url(r'^doc_cloud/(?P<doc_id>[\w\d_-]+)/$',
                                      views.doc_cloud_detail, name='foia-doc-cloud-detail'),
    url(r'^update/%s/$' % foia_url,   views.update, name='foia-update'),
    url(r'^fix/%s/$' % foia_url,      views.fix, name='foia-fix'),
    url(r'^appeal/%s/$' % foia_url,   views.appeal, name='foia-appeal'),
    url(r'^flag/%s/$' % foia_url,     views.flag, name='foia-flag'),
    url(r'^add_note/%s/$' % foia_url, views.note, name='foia-note'),
    url(r'^delete/%s/$' % foia_url,   views.delete, name='foia-delete'),
    url(r'^embargo/%s/$' % foia_url,  views.embargo, name='foia-embargo'),
    url(r'^feeds/submitted/$',        LatestSubmittedRequests(), name='foia-submitted-feed'),
    url(r'^feeds/completed/$',        LatestDoneRequests(), name='foia-done-feed'),
)
