"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns
from django.views.generic import list_detail

from  foia import views
from foia.models import FOIARequest

foia_request_qs = {'queryset': FOIARequest.objects.all()}

urlpatterns = patterns('',
    (r'^view/(?P<object_id>\d+)/$',           list_detail.object_detail, foia_request_qs),
    (r'^list/$',                              list_detail.object_list, foia_request_qs),
    (r'^list/(?P<user_name>[A-Za-z0-9_]+)/$', views.list_by_user),
    (r'^new/$',                               views.create_foiarequest),
    (r'^update/(?P<object_id>\d+)/$',         views.update_foiarequest),
)
