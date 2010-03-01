"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns
from django.views.generic import list_detail

from foia import views
from foia.models import FOIARequest

foia_qs = {'queryset': FOIARequest.objects.all()}

urlpatterns = patterns('',
    (r'^list/$',                               list_detail.object_list, foia_qs),
    (r'^list/(?P<user_name>[A-Za-z0-9_i]+)/$', views.list_by_user),
    (r'^new/$',                                views.create),
    (r'^view/(?P<user_name>[A-Za-z0-9_]+)/(?P<slug>[A-Za-z0-9_-]+)/$',
                                               views.detail),
    (r'^update/(?P<user_name>[A-Za-z0-9_]+)/(?P<slug>[A-Za-z0-9_-]+)/$',
                                               views.update),
)
