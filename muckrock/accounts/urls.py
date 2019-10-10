"""
URL mappings for the accounts application
"""

# Django
from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

# MuckRock
import muckrock.accounts.views as views

urlpatterns = [
    url(r'^$', views.AccountsView.as_view(), name='accounts'),
    url(
        r'^upgrade/$',
        views.AccountsUpgradeView.as_view(),
        name='accounts-upgrade',
    ),
    url(
        r'^signup/$',
        RedirectView.as_view(
            url=settings.SQUARELET_URL + '/accounts/signup/?intent=muckrock'
        ),
        name='accounts-signup'
    ),
    url(
        r'^login/$',
        RedirectView.as_view(
            url=reverse_lazy('social:begin', kwargs={
                'backend': 'squarelet'
            }),
            query_string=True
        ),
        name='acct-login'
    ),
    url(r'^logout/$', views.account_logout, name='acct-logout'),
    url(
        r'^reset_pw/$',
        RedirectView.as_view(
            url=settings.SQUARELET_URL + '/accounts/password/reset/'
        ),
        name='acct-reset-pw'
    ),
    url(
        r'^profile/$',
        login_required(views.ProfileView.as_view()),
        name='acct-my-profile'
    ),
    url(
        r'^profile/(?P<username>[\w\-.@ ]+)/$',
        views.ProfileView.as_view(),
        name='acct-profile'
    ),
    url(
        r'^contact_user/(?P<idx>\d+)/$',
        views.contact_user,
        name='acct-contact-user'
    ),
    url(
        r'^notifications/$',
        views.NotificationList.as_view(),
        name='acct-notifications'
    ),
    url(
        r'^notifications/unread/$',
        views.UnreadNotificationList.as_view(),
        name='acct-notifications-unread'
    ),
    url(r'^settings/$', views.ProfileSettings.as_view(), name='acct-settings'),
    url(r'^proxies/$', views.ProxyList.as_view(), name='accounts-proxies'),
    url(r'^stripe_webhook_v2/$', views.stripe_webhook, name='acct-webhook-v2'),
    url(
        r'agency_login/(?P<agency_slug>[\w\d_-]+)-(?P<agency_idx>\d+)/'
        r'(?P<foia_slug>[\w\d_-]+)-(?P<foia_idx>\d+)/$',
        views.agency_redirect_login,
        name='acct-agency-redirect-login'
    ),
    url(r'^rp_iframe/$', views.rp_iframe, name='acct-rp-iframe'),
    url(r'^', include('social_django.urls', namespace='social')),
]
