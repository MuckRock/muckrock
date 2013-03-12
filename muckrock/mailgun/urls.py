"""
URL mappings for mailgun
"""

from django.conf.urls.defaults import patterns, url

from muckrock.mailgun import views

urlpatterns = patterns('',
        url(r'^request/(?P<mail_id>\d+-\d{8})/$', views.handle_request, name='mailgun-request'),
        url(r'^fax/$',                            views.fax, name='mailgun-fax'),
)
