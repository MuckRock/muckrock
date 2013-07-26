"""
URL mappings for the crowdfund application
"""

from django.conf.urls.defaults import patterns, url

from muckrock.crowdfund import views

urlpatterns = patterns('',
    url(r'^contirbute/(?P<pk>\d+)/$', views.contribute_request, name='crowdfund-contribute-reqs'),
    )
