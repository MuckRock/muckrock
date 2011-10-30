"""
URL mappings for the accounts application
"""

from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
import django.contrib.auth.views as auth_views

import accounts.views

urlpatterns = patterns('',
    url(r'^login/$',             auth_views.login, name='acct-login'),
    url(r'^logout/$',            auth_views.logout, name='acct-logout'),
    url(r'^profile/$',           login_required(accounts.views.profile), name='acct-my-profile'),
    url(r'^profile/(?P<user_name>[\w\d_.@]+)/$',
                                 accounts.views.profile, name='acct-profile'),
    url(r'^register/$',          accounts.views.register, name='acct-register'),
    url(r'^register/free/$',     accounts.views.register_free, name='acct-register-free'),
    url(r'^register/pro/$',      accounts.views.register_pro, name='acct-register-pro'),
    url(r'^update/$',            accounts.views.update, name='acct-update'),
    url(r'^update_cc/$',         accounts.views.update_cc, name='acct-update-cc'),
    url(r'^manage_subsc/$',      accounts.views.manage_subsc, name='acct-manage-subsc'),
    url(r'^buy_requests/$',      accounts.views.buy_requests, name='acct-buy-requests'),
    url(r'^change_pw/$',         auth_views.password_change, name='acct-change-pw'),
    url(r'^change_pw_done/$',    auth_views.password_change_done, name='acct-change-pw-done'),
    url(r'^reset_pw/$',          auth_views.password_reset, name='acct-reset-pw'),
    url(r'^reset_pw_done/$',     auth_views.password_reset_done, name='acct-reset-pw-done'),
    url(r'^reset_pw_complete/$', auth_views.password_reset_complete, name='acct-reset-pw-complete'),
    url(r'^reset_pw/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                                 auth_views.password_reset_confirm, name='acct-reset-pw-confirm'),
)
