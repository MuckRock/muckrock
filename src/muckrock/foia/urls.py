"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns, url

from pingback import register_pingback

from foia import views
from foia.feeds import LatestSubmittedRequests, LatestDoneRequests
from foia.pingbacks import pingback_foia_handler

foia_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

register_pingback(views.detail, pingback_foia_handler)

urlpatterns = patterns('',
    url(r'^list/$',                   views.list_, name='foia-list'),
    url(r'^list/user/(?P<user_name>[\w\d_]+)/$',
                                      views.list_by_user, name='foia-list-user'),
    url(r'^list/(?P<sort_order>asc|desc)/(?P<field>[\w]+)/$',
                                      views.sorted_list, name='foia-sorted-list'),
    url(r'^new/$',                    views.create,
                                      name='foia-create'),
    url(r'^view/%s/$' % foia_url,     views.detail, name='foia-detail'),
    url(r'^doc_cloud/(?P<doc_id>[\w\d_-]+)/$',
                                      views.doc_cloud_detail, name='foia-doc-cloud-detail'),
    url(r'^update/$',                 views.update_list, name='foia-update-list'),
    url(r'^update/%s/$' % foia_url,   views.update, name='foia-update'),
    url(r'^delete/%s/$' % foia_url,   views.delete, name='foia-delete'),
    url(r'^feeds/submitted/$',        LatestSubmittedRequests(), name='foia-submitted-feed'),
    url(r'^feeds/completed/$',        LatestDoneRequests(), name='foia-done-feed'),
)
