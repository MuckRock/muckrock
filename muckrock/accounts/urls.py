"""
URL mappings for the accounts application
"""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
import django.contrib.auth.views as auth_views

import muckrock.accounts.views as views

# pylint: disable=bad-whitespace

urlpatterns = patterns('',
    url(r'^login/$',             auth_views.login, {'template_name': 'user/login.html'}, name='acct-login'),
    url(r'^logout/$',            auth_views.logout, {'template_name': 'user/logout.html'}, name='acct-logout'),
    url(r'^profile/$',           login_required(views.profile), name='acct-my-profile'),
    url(r'^profile/(?P<user_name>[\w\d_.@ ]+)/$',
                                 views.profile, name='acct-profile'),
    url(r'^register/$',          views.register, name='acct-register'),
    url(r'^register/free/$',     views.register_free, name='acct-register-free'),
    url(r'^register/pro/$',      views.register_pro, name='acct-register-pro'),
    url(r'^update/$',            views.update, name='acct-update'),
    url(r'^update_cc/$',         views.update_cc, name='acct-update-cc'),
    url(r'^manage_subsc/$',      views.manage_subsc, name='acct-manage-subsc'),
    url(r'^buy_requests/$',      views.buy_requests, name='acct-buy-requests'),
    url(r'^stripe_webhook/$',    views.stripe_webhook, name='acct-webhook'),
    url(r'^stripe_webhook_v2/$', views.stripe_webhook_v2, name='acct-webhook-v2'),
    url(r'^change_pw/$',         auth_views.password_change, name='acct-change-pw'),
    url(r'^change_pw_done/$',    auth_views.password_change_done, name='acct-change-pw-done'),
    url(r'^reset_pw/$',          auth_views.password_reset, name='acct-reset-pw'),
    url(r'^reset_pw_done/$',     auth_views.password_reset_done, name='acct-reset-pw-done'),
    url(r'^reset_pw_complete/$', auth_views.password_reset_complete, name='acct-reset-pw-complete'),
    url(r'^reset_pw/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                                 auth_views.password_reset_confirm, name='acct-reset-pw-confirm'),
)
