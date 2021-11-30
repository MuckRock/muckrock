"""
FOIA Machine urls
"""

# Django
from django.conf import settings
from django.conf.urls import include
from django.urls import re_path
from django.views.defaults import page_not_found, server_error
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve

# Third Party
import debug_toolbar

# MuckRock
from muckrock.accounts import views as account_views
from muckrock.agency.urls import agency_url
from muckrock.agency.views import AgencyAutocomplete
from muckrock.foiamachine import views
from muckrock.jurisdiction.urls import jur_url
from muckrock.jurisdiction.views import JurisdictionAutocomplete


def handler404(request, exception):
    """404 handler"""
    return page_not_found(request, exception, template_name="foiamachine/404.html")


def handler500(request):
    """500 handler"""
    return server_error(request, template_name="foiamachine/500.html")


urlpatterns = [
    re_path(r"^$", views.Homepage.as_view(), name="index"),
    re_path(
        r"^accounts/signup/$",
        RedirectView.as_view(
            url=settings.SQUARELET_URL + "/accounts/signup/?intent=foiamachine"
        ),
        name="signup",
    ),
    re_path(r"^accounts/login/$", views.LoginView.as_view(), name="login"),
    re_path(r"^accounts/logout/$", views.account_logout, name="acct-logout"),
    re_path(r"^accounts/profile/$", views.Profile.as_view(), name="profile"),
    re_path(
        r"^foi/create/$",
        views.FoiaMachineRequestCreateView.as_view(),
        name="foi-create",
    ),
    re_path(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/$",
        views.FoiaMachineRequestDetailView.as_view(),
        name="foi-detail",
    ),
    re_path(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/update/$",
        views.FoiaMachineRequestUpdateView.as_view(),
        name="foi-update",
    ),
    re_path(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/delete/$",
        views.FoiaMachineRequestDeleteView.as_view(),
        name="foi-delete",
    ),
    re_path(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/share/$",
        views.FoiaMachineRequestShareView.as_view(),
        name="foi-share",
    ),
    re_path(
        r"^foi/(?P<foi_slug>[\w-]+)-(?P<foi_pk>\d+)/comms/create/$",
        views.FoiaMachineCommunicationCreateView.as_view(),
        name="comm-create",
    ),
    re_path(
        r"^foi/(?P<foi_slug>[\w-]+)-(?P<foi_pk>\d+)/comms/(?P<pk>\d+)/update/$",
        views.FoiaMachineCommunicationUpdateView.as_view(),
        name="comm-update",
    ),
    re_path(
        r"^foi/(?P<foi_slug>[\w-]+)-(?P<foi_pk>\d+)/comms/(?P<pk>\d+)/delete/$",
        views.FoiaMachineCommunicationDeleteView.as_view(),
        name="comm-delete",
    ),
    re_path(r"^agency/%s/$" % agency_url, views.agency_detail, name="agency-detail"),
    re_path(
        r"^jurisdiction/%s/$" % jur_url,
        views.jurisdiction_detail,
        name="jurisdiction-detail",
    ),
    re_path(
        r"^agency-autocomplete/$",
        AgencyAutocomplete.as_view(),
        name="agency-autocomplete",
    ),
    re_path(
        r"^jurisdiction-autocomplete/$",
        JurisdictionAutocomplete.as_view(),
        name="jurisdiction-autocomplete",
    ),
    re_path(r"^__debug__/", include(debug_toolbar.urls)),
    re_path(r"^accounts/", include("social_django.urls", namespace="social")),
    re_path(r"^rp_iframe/$", account_views.rp_iframe, name="acct-rp-iframe"),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        re_path(r"^500/$", TemplateView.as_view(template_name="foiamachine/500.html")),
        re_path(r"^404/$", TemplateView.as_view(template_name="foiamachine/404.html")),
    ]
