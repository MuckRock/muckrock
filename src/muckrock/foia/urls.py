"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns
from django.views.generic import list_detail

from foia import views
from foia.models import FOIARequest

foia_qs = {'queryset': FOIARequest.objects.all()}

urlpatterns = patterns('',
    (r'^$',                              list_detail.object_list, foia_qs),
    (r'^list/$',                         list_detail.object_list, foia_qs),
    (r'^list/(?P<user_name>[\w\d_]+)/$', views.list_by_user),
    (r'^new/$',                          views.create),
    (r'^view/(?P<user_name>[\w\d_]+)/(?P<slug>[\w\d_-]+)/$',
                                         views.detail),
    (r'^view/(?P<user_name>[\w\d_]+)/(?P<slug>[\w\d_-]+)/doc/(?P<page>\d+)/$',
                                         views.document_detail),
    (r'^update/(?P<user_name>[\w\d_]+)/(?P<slug>[\w\d_-]+)/$',
                                         views.update),
)
