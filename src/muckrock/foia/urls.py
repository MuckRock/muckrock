"""
URL mappings for the FOIA application
"""

from django.conf.urls.defaults import patterns
from django.views.generic import list_detail

from foia.models import FOIARequest

urlpatterns = patterns('',
    (r'^list/$', list_detail.object_list, {'queryset': FOIARequest.objects.all()}),
    (r'^view/(?P<object_id>\d+)/$', list_detail.object_detail,
        {'queryset': FOIARequest.objects.all()}),
)
