"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from foia import views
from foia.feeds import LatestSubmittedRequests, LatestDoneRequests
from foia.forms import foia_wizard, wizard_extra_context

foia_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns('',
    url(r'^list/$',                     views.list_, name='foia-list'),
    url(r'^list/user/(?P<user_name>[\w\d_]+)/$',
                                        views.list_by_user, name='foia-list-user'),
    url(r'^list/(?P<sort_order>asc|desc)/(?P<field>[\w]+)/$',
                                        views.sorted_list, name='foia-sorted-list'),
    url(r'^new/$',                      login_required(foia_wizard),
                                        kwargs={'extra_context': wizard_extra_context},
                                        name='foia-create'),
    url(r'^view/%s/$' % foia_url,       views.detail, name='foia-detail'),
    url(r'^view/%s/doc/(?P<page>\d+)/$' % foia_url,
                                        views.document_detail, name='foia-doc-detail'),
    url(r'^update/$',                   views.update_list, name='foia-update-list'),
    url(r'^update/%s/$' % foia_url,     views.update, name='foia-update'),
    url(r'^delete/%s/$' % foia_url,     views.delete, name='foia-delete'),
    url(r'^feeds/submitted/$',          LatestSubmittedRequests(), name='foia-submitted-feed'),
    url(r'^feeds/completed/$',          LatestDoneRequests(), name='foia-done-feed'),
)
