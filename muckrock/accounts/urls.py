"""
URL mappings for the accounts application
"""

# Django
from django.conf import settings
from django.conf.urls import include
from django.contrib.auth.decorators import login_required
from django.urls import re_path, reverse_lazy
from django.views.generic import RedirectView

# MuckRock
import muckrock.accounts.views as views

urlpatterns = [
    re_path(r"^$", views.AccountsView.as_view(), name="accounts"),
    re_path(
        r"^upgrade/$", views.AccountsUpgradeView.as_view(), name="accounts-upgrade"
    ),
    re_path(
        r"^signup/$",
        RedirectView.as_view(
            url=settings.SQUARELET_URL + "/accounts/signup/?intent=muckrock"
        ),
        name="accounts-signup",
    ),
    re_path(
        r"^login/$",
        RedirectView.as_view(
            url=reverse_lazy("social:begin", kwargs={"backend": "squarelet"}),
            query_string=True,
        ),
        name="acct-login",
    ),
    re_path(r"^logout/$", views.account_logout, name="acct-logout"),
    re_path(
        r"^reset_pw/$",
        RedirectView.as_view(url=settings.SQUARELET_URL + "/accounts/password/reset/"),
        name="acct-reset-pw",
    ),
    re_path(
        r"^profile/$",
        login_required(views.ProfileView.as_view()),
        name="acct-my-profile",
    ),
    re_path(
        r"^profile/(?P<username>[\w\-.@ ]+)/$",
        views.ProfileView.as_view(),
        name="acct-profile",
    ),
    re_path(
        r"^contact_user/(?P<idx>\d+)/$", views.contact_user, name="acct-contact-user"
    ),
    re_path(
        r"^notifications/$", views.NotificationList.as_view(), name="acct-notifications"
    ),
    re_path(
        r"^notifications/unread/$",
        views.UnreadNotificationList.as_view(),
        name="acct-notifications-unread",
    ),
    re_path(r"^settings/$", views.ProfileSettings.as_view(), name="acct-settings"),
    re_path(r"^proxies/$", views.ProxyList.as_view(), name="accounts-proxies"),
    re_path(r"^stripe_webhook_v2/$", views.stripe_webhook, name="acct-webhook-v2"),
    re_path(
        r"agency_login/(?P<agency_slug>[\w\d_-]+)-(?P<agency_idx>\d+)/"
        r"(?P<foia_slug>[\w\d_-]+)-(?P<foia_idx>\d+)/$",
        views.agency_redirect_login,
        name="acct-agency-redirect-login",
    ),
    re_path(r"^rp_iframe/$", views.rp_iframe, name="acct-rp-iframe"),
    re_path(r"^", include("social_django.urls", namespace="social")),
    re_path(
        r"^user-autocomplete/$",
        views.UserAutocomplete.as_view(),
        name="user-autocomplete",
    ),
]
