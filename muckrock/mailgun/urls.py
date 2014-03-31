"""
URL mappings for mailgun
"""

from django.conf.urls import patterns, url

from muckrock.mailgun import views

# pylint: disable=bad-whitespace

urlpatterns = patterns('',
        url(r'^request/(?P<mail_id>\d+-\d{3,10})/$', views.handle_request, name='mailgun-request'),
        url(r'^fax/$',                               views.fax, name='mailgun-fax'),
        url(r'^bounces/$',                           views.bounces, name='mailgun-bounces'),
)
