"""
URL mappings for the accounts application
"""

from django.conf.urls.defaults import patterns
from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required
import django.contrib.auth.views as auth_views

import accounts.views

urlpatterns = patterns('',
    (r'^login/$',             auth_views.login),
    (r'^logout/$',            auth_views.logout),
    (r'^profile/$',           login_required(direct_to_template),
        {'template': 'registration/profile.html'}),
    (r'^register/$',          accounts.views.register),
    (r'^update/$',            accounts.views.update),
    (r'^change_pw/$',         auth_views.password_change),
    (r'^change_pw_done/$',    auth_views.password_change_done),
    (r'^reset_pw/$',          auth_views.password_reset),
    (r'^reset_pw_done/$',     auth_views.password_reset_done),
    (r'^reset_pw_complete/$', auth_views.password_reset_complete),
    (r'^reset_pw/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                               auth_views.password_reset_confirm),
)
