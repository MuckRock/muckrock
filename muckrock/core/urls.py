"""
URL mappings for muckrock project
"""

# Django
import django.contrib.sitemaps.views
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path
from django.views import static
from django.views.generic.base import RedirectView, TemplateView

# Third Party
import debug_toolbar
from dashing.utils import router as dashing_router
from rest_framework.routers import DefaultRouter

# MuckRock
import muckrock.accounts.viewsets
import muckrock.agency.viewsets
import muckrock.core.views as views
import muckrock.crowdsource.viewsets
import muckrock.foia.viewsets
import muckrock.jurisdiction.urls
import muckrock.jurisdiction.viewsets
import muckrock.news.viewsets
import muckrock.project.viewsets
import muckrock.qanda.views
import muckrock.task.viewsets
from muckrock.agency.sitemap import AgencySitemap
from muckrock.core.sitemap import FlatPageSitemap
from muckrock.core.views import handler500  # pylint: disable=unused-import
from muckrock.foia.sitemap import FoiaSitemap
from muckrock.foia.views.communications import FOIACommunicationDirectAgencyView
from muckrock.jurisdiction.sitemap import JurisdictionSitemap
from muckrock.news.sitemap import ArticleSitemap
from muckrock.project.sitemap import ProjectSitemap
from muckrock.qanda.sitemap import QuestionSitemap

admin.site.index_template = "admin/custom_index.html"

sitemaps = {
    "FOIA": FoiaSitemap,
    "News": ArticleSitemap,
    "Agency": AgencySitemap,
    "Jurisdiction": JurisdictionSitemap,
    "Question": QuestionSitemap,
    "Project": ProjectSitemap,
    "Flatpages": FlatPageSitemap,
}

router = DefaultRouter()
router.register(
    r"jurisdiction",
    muckrock.jurisdiction.viewsets.JurisdictionViewSet,
    "api-jurisdiction",
)
router.register(r"agency", muckrock.agency.viewsets.AgencyViewSet, "api-agency")
router.register(r"foia", muckrock.foia.viewsets.FOIARequestViewSet, "api-foia")
router.register(
    r"exemption", muckrock.jurisdiction.viewsets.ExemptionViewSet, "api-exemption"
)
router.register(
    r"statistics", muckrock.accounts.viewsets.StatisticsViewSet, "api-statistics"
)
router.register(
    r"communication",
    muckrock.foia.viewsets.FOIACommunicationViewSet,
    "api-communication",
)
router.register(r"user", muckrock.accounts.viewsets.UserViewSet, "api-user")
router.register(r"news", muckrock.news.viewsets.ArticleViewSet, "api-news")
router.register(r"photos", muckrock.news.viewsets.PhotoViewSet, "api-photos")
router.register(r"task", muckrock.task.viewsets.TaskViewSet, "api-task")
router.register(
    r"orphantask", muckrock.task.viewsets.OrphanTaskViewSet, "api-orphantask"
)
router.register(
    r"snailmailtask", muckrock.task.viewsets.SnailMailTaskViewSet, "api-snailmailtask"
)
router.register(
    r"flaggedtask", muckrock.task.viewsets.FlaggedTaskViewSet, "api-flaggedtask"
)
router.register(
    r"newagencytask", muckrock.task.viewsets.NewAgencyTaskViewSet, "api-newagencytask"
)
router.register(
    r"responsetask", muckrock.task.viewsets.ResponseTaskViewSet, "api-responsetask"
)
router.register(
    r"assignment-responses",
    muckrock.crowdsource.viewsets.CrowdsourceResponseViewSet,
    "api-crowdsource-response",
)
router.register(r"project", muckrock.project.viewsets.ProjectViewSet, "api-project")

urlpatterns = [
    url(r"^$", views.homepage, name="index"),
    url(r"^reset_cache/$", views.reset_homepage_cache, name="reset-cache"),
    url(r"^accounts/", include("muckrock.accounts.urls")),
    url(r"^foi/", include("muckrock.foia.urls")),
    url(r"^news/", include("muckrock.news.urls")),
    url(r"^newsletter-post/$", views.NewsletterSignupView.as_view(), name="newsletter"),
    url(r"^mailgun/", include("muckrock.mailgun.urls")),
    url(r"^agency/", include("muckrock.agency.urls")),
    url(r"^place/", include(muckrock.jurisdiction.urls.urlpatterns)),
    url(r"^jurisdiction/", include(muckrock.jurisdiction.urls.old_urlpatterns)),
    url(r"^questions/", include("muckrock.qanda.urls")),
    url(r"^crowdfund/", include("muckrock.crowdfund.urls")),
    url(r"^assignment/", include("muckrock.crowdsource.urls")),
    url(r"^task/", include("muckrock.task.urls")),
    url(r"^tags/", include("muckrock.tags.urls")),
    url(r"^organization/", include("muckrock.organization.urls")),
    url(r"^project/", include("muckrock.project.urls")),
    url(r"^fine-uploader/", include("muckrock.fine_uploader.urls")),
    url(r"^communication/", include("muckrock.communication.urls")),
    url(r"^squarelet/", include("muckrock.squarelet.urls")),
    url(r"^admin/", admin.site.urls),
    url(r"^search/$", views.SearchView.as_view(), name="search"),
    url(r"^api_v1/", include(router.urls)),
    url(r"^robots\.txt$", include("robots.urls")),
    url(
        r"^favicon.ico$",
        RedirectView.as_view(url=settings.STATIC_URL + "icons/favicon.ico"),
    ),
    url(
        r"^sitemap\.xml$",
        django.contrib.sitemaps.views.index,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.index",
    ),
    url(
        r"^sitemap-(?P<section>.+)\.xml$",
        django.contrib.sitemaps.views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    url(r"^news-sitemaps/", include("news_sitemaps.urls")),
    url(r"^__debug__/", include(debug_toolbar.urls)),
    url(r"^donate/$", views.DonationFormView.as_view(), name="donate"),
    url(r"^donate/thanks/$", views.DonationThanksView.as_view(), name="donate-thanks"),
    url(r"^landing/$", views.LandingView.as_view(), name="landing"),
    url(r"^hijack/", include("hijack.urls")),
    url(r"^opensearch/", include("opensearch.urls")),
    url(r"^dashboard/", include(dashing_router.urls)),
    path(
        "respond/<int:idx>/",
        FOIACommunicationDirectAgencyView.as_view(),
        name="communication-direct-agency",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        url(
            r"^media/(?P<path>.*)$",
            static.serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
        url(r"^500/$", TemplateView.as_view(template_name="500.html")),
        url(r"^404/$", TemplateView.as_view(template_name="404.html")),
        url(r"^silk/", include("silk.urls", namespace="silk")),
    ]
