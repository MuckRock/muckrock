"""
URL mappings for the jurisdiction application
"""

from django.conf.urls.defaults import patterns, url

from jurisdiction import views

urlpatterns = patterns('',
    url(r'^view/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)/$', views.detail, name='jurisdiction-detail'),
)

