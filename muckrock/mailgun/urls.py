"""
URL mappings for mailgun
"""

from django.conf.urls import patterns, url

from muckrock.mailgun import views

urlpatterns = patterns(
    '',
    url(
        r'^request/(?P<mail_id>\d+-\d{3,10})/$',
        views.handle_request,
        name='mailgun-request'
    ),
    url(
        r'^fax/$',
        views.fax,
        name='mailgun-fax'
    ),
    url(
        r'^catch_all/(?P<address>.*)/$',
        views.catch_all,
        name='mailgun-catchall'
    ),
    url(
        r'^bounces/$',
        views.bounces,
        name='mailgun-bounces'
    ),
    url(
        r'^opened/$',
        views.opened,
        name='mailgun-opened'
    ),
)
