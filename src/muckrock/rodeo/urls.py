"""
URL mappings for the Rodeo application
"""


from django.conf.urls.defaults import patterns, url

from rodeo import views

urlpatterns = patterns('',
    url(r'^rodeo/(?P<doc_id>[\w\d_-]+)/(?P<rodeo_pk>\d+)/$', views.main, name='rodeo-detail'),
)
