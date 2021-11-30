"""
URL mappings for muckrock project
"""

# Django
import django.contrib.sitemaps.views
from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.urls import path, re_path
from django.views import static
from django.views.generic.base import RedirectView, TemplateView

# Third Party
import debug_toolbar
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
    re_path(r"^$", views.homepage, name="index"),
    re_path(r"^reset_cache/$", views.reset_homepage_cache, name="reset-cache"),
    re_path(r"^accounts/", include("muckrock.accounts.urls")),
    re_path(r"^foi/", include("muckrock.foia.urls")),
    re_path(r"^news/", include("muckrock.news.urls")),
    re_path(
        r"^newsletter-post/$", views.NewsletterSignupView.as_view(), name="newsletter"
    ),
    re_path(r"^mailgun/", include("muckrock.mailgun.urls")),
    re_path(r"^agency/", include("muckrock.agency.urls")),
    re_path(r"^place/", include(muckrock.jurisdiction.urls.urlpatterns)),
    re_path(r"^jurisdiction/", include(muckrock.jurisdiction.urls.old_urlpatterns)),
    re_path(r"^questions/", include("muckrock.qanda.urls")),
    re_path(r"^crowdfund/", include("muckrock.crowdfund.urls")),
    re_path(r"^assignment/", include("muckrock.crowdsource.urls")),
    re_path(r"^task/", include("muckrock.task.urls")),
    re_path(r"^tags/", include("muckrock.tags.urls")),
    re_path(r"^organization/", include("muckrock.organization.urls")),
    re_path(r"^project/", include("muckrock.project.urls")),
    re_path(r"^fine-uploader/", include("muckrock.fine_uploader.urls")),
    re_path(r"^communication/", include("muckrock.communication.urls")),
    re_path(r"^squarelet/", include("muckrock.squarelet.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^search/$", views.SearchView.as_view(), name="search"),
    re_path(r"^api_v1/", include(router.urls)),
    re_path(r"^robots\.txt$", include("robots.urls")),
    re_path(
        r"^favicon.ico$",
        RedirectView.as_view(url=settings.STATIC_URL + "icons/favicon.ico"),
    ),
    re_path(
        r"^sitemap\.xml$",
        django.contrib.sitemaps.views.index,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.index",
    ),
    re_path(
        r"^sitemap-(?P<section>.+)\.xml$",
        django.contrib.sitemaps.views.sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    re_path(r"^news-sitemaps/", include("news_sitemaps.urls")),
    re_path(r"^__debug__/", include(debug_toolbar.urls)),
    re_path(r"^donate/$", views.DonationFormView.as_view(), name="donate"),
    re_path(
        r"^donate/thanks/$", views.DonationThanksView.as_view(), name="donate-thanks"
    ),
    re_path(r"^landing/$", views.LandingView.as_view(), name="landing"),
    re_path(r"^hijack/", include("hijack.urls")),
    re_path(r"^opensearch/", include("opensearch.urls")),
    path(
        "respond/<int:idx>/",
        FOIACommunicationDirectAgencyView.as_view(),
        name="communication-direct-agency",
    ),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            static.serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
        re_path(r"^500/$", TemplateView.as_view(template_name="500.html")),
        re_path(r"^404/$", TemplateView.as_view(template_name="404.html")),
        # re_path(r"^silk/", include("silk.urls", namespace="silk")),
    ]
