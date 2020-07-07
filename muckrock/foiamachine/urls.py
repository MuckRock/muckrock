"""
FOIA Machine urls
"""

# Django
from django.conf import settings
from django.conf.urls import include, url
from django.views.defaults import page_not_found, server_error
from django.views.generic import RedirectView, TemplateView
from django.views.static import serve

# Third Party
import debug_toolbar

# MuckRock
from muckrock.accounts import views as account_views
from muckrock.agency.urls import agency_url
from muckrock.foiamachine import views
from muckrock.jurisdiction.urls import jur_url


def handler404(request, exception):
    """404 handler"""
    return page_not_found(request, exception, template_name="foiamachine/404.html")


def handler500(request):
    """500 handler"""
    return server_error(request, template_name="foiamachine/500.html")


urlpatterns = [
    url(r"^$", views.Homepage.as_view(), name="index"),
    url(
        r"^accounts/signup/$",
        RedirectView.as_view(
            url=settings.SQUARELET_URL + "/accounts/signup/?intent=foiamachine"
        ),
        name="signup",
    ),
    url(r"^accounts/login/$", views.LoginView.as_view(), name="login"),
    url(r"^accounts/logout/$", views.account_logout, name="acct-logout"),
    url(r"^accounts/profile/$", views.Profile.as_view(), name="profile"),
    url(
        r"^foi/create/$",
        views.FoiaMachineRequestCreateView.as_view(),
        name="foi-create",
    ),
    url(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/$",
        views.FoiaMachineRequestDetailView.as_view(),
        name="foi-detail",
    ),
    url(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/update/$",
        views.FoiaMachineRequestUpdateView.as_view(),
        name="foi-update",
    ),
    url(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/delete/$",
        views.FoiaMachineRequestDeleteView.as_view(),
        name="foi-delete",
    ),
    url(
        r"^foi/(?P<slug>[\w-]+)-(?P<pk>\d+)/share/$",
        views.FoiaMachineRequestShareView.as_view(),
        name="foi-share",
    ),
    url(
        r"^foi/(?P<foi_slug>[\w-]+)-(?P<foi_pk>\d+)/comms/create/$",
        views.FoiaMachineCommunicationCreateView.as_view(),
        name="comm-create",
    ),
    url(
        r"^foi/(?P<foi_slug>[\w-]+)-(?P<foi_pk>\d+)/comms/(?P<pk>\d+)/update/$",
        views.FoiaMachineCommunicationUpdateView.as_view(),
        name="comm-update",
    ),
    url(
        r"^foi/(?P<foi_slug>[\w-]+)-(?P<foi_pk>\d+)/comms/(?P<pk>\d+)/delete/$",
        views.FoiaMachineCommunicationDeleteView.as_view(),
        name="comm-delete",
    ),
    url(r"^agency/%s/$" % agency_url, views.agency_detail, name="agency-detail"),
    url(
        r"^jurisdiction/%s/$" % jur_url,
        views.jurisdiction_detail,
        name="jurisdiction-detail",
    ),
    url(r"^autocomplete/", include("autocomplete_light.urls")),
    url(r"^__debug__/", include(debug_toolbar.urls)),
    url(r"^accounts/", include("social_django.urls", namespace="social")),
    url(r"^rp_iframe/$", account_views.rp_iframe, name="acct-rp-iframe"),
]

if settings.DEBUG:
    urlpatterns += [
        url(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        url(r"^500/$", TemplateView.as_view(template_name="foiamachine/500.html")),
        url(r"^404/$", TemplateView.as_view(template_name="foiamachine/404.html")),
    ]
