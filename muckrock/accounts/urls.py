"""
URL mappings for the accounts application
"""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView
import django.contrib.auth.views as auth_views

import muckrock.accounts.views as views

# pylint: disable=bad-whitespace

urlpatterns = patterns(
    '',
    url(
        r'^login/$',
        auth_views.login,
        {'template_name': 'forms/account/login.html'},
        name='acct-login'
    ),
    url(
        r'^logout/$',
        views.account_logout,
        name='acct-logout'
    ),
    url(
        r'^profile/$',
        login_required(views.profile),
        name='acct-my-profile'
    ),
    url(
        r'^profile/(?P<user_name>[\w\-.@ ]+)/$',
        views.profile,
        name='acct-profile'
    ),
    url(r'^register/$', views.register, name='acct-register'),
    url(r'^subscribe/$', views.subscribe, name='acct-subscribe'),
    url(r'^update/$', views.update, name='acct-update'),
    url(r'^verify_email/$', views.verify_email, name='acct-verify-email'),
    url(r'^buy_requests/$', views.buy_requests, name='acct-buy-requests'),
    url(r'^stripe_webhook_v2/$', views.stripe_webhook_v2, name='acct-webhook-v2'),
    url(
        r'^change_pw/$',
        auth_views.password_change,
        {'template_name': 'forms/account/pw_change.html',
         'post_change_redirect': 'acct-change-pw-done'},
        name='acct-change-pw'
    ),
    url(
        r'^change_pw_done/$',
        auth_views.password_change_done,
        {'template_name': 'forms/account/pw_change_done.html'},
        name='acct-change-pw-done'
    ),
    url(
        r'^reset_pw/$',
        auth_views.password_reset,
        {'template_name': 'forms/account/pw_reset_part1.html',
         'post_reset_redirect': 'acct-reset-pw-done'},
        name='acct-reset-pw'
    ),
    url(
        r'^reset_pw_done/$',
        auth_views.password_reset_done,
        {'template_name': 'forms/account/pw_reset_part1_done.html'},
        name='acct-reset-pw-done'
    ),
    url(
        r'^reset_pw/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        {'template_name': 'forms/account/pw_reset_part2.html'},
        name='password_reset_confirm'
    ),
    url(
        r'^reset_pw_complete/$',
        auth_views.password_reset_complete,
        {'template_name': 'forms/account/pw_reset_part2_done.html'},
        name='password_reset_complete'
    ),
    # REDIRECT VIEWS
    url(
        r'^register/free/$',
        RedirectView.as_view(url='/accounts/register/'),
        name='acct-register-free'
    ),
    url(
        r'^register/pro/$',
        RedirectView.as_view(url='/accounts/subscribe/'),
        name='acct-register-pro'
    ),
    url(
        r'^manage_subsc/$',
        RedirectView.as_view(url='/accounts/subscribe/'),
        name='acct-manage-subsc'
    ),
)
