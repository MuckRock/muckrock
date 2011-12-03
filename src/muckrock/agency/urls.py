"""
URL mappings for the Agency application
"""

from django.conf.urls.defaults import patterns, url

from agency import views

urlpatterns = patterns('',
    url(r'^update/(?P<idx>\d+)/$', views.update, name='agency-update'),
)
