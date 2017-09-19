"""
URL mappings for muckrock project
"""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
import django.contrib.sitemaps.views
from django.views.generic.base import RedirectView, TemplateView
from django.views import static

from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
import dbsettings.urls
import debug_toolbar

import muckrock.accounts.views
import muckrock.agency.views
import muckrock.foia.viewsets
import muckrock.jurisdiction.viewsets
import muckrock.jurisdiction.urls
import muckrock.news.views
import muckrock.qanda.views
import muckrock.task.viewsets
import muckrock.views as views
from muckrock.agency.sitemap import AgencySitemap
from muckrock.foia.sitemap import FoiaSitemap
from muckrock.jurisdiction.sitemap import JurisdictionSitemap
from muckrock.news.sitemap import ArticleSitemap
from muckrock.project.sitemap import ProjectSitemap
from muckrock.qanda.sitemap import QuestionSitemap
from muckrock.views import handler500 # pylint: disable=unused-import

admin.site.index_template = 'admin/custom_index.html'

sitemaps = {
    'FOIA': FoiaSitemap,
    'News': ArticleSitemap,
    'Agency': AgencySitemap,
    'Jurisdiction': JurisdictionSitemap,
    'Question': QuestionSitemap,
    'Project': ProjectSitemap,
}

router = DefaultRouter()
router.register(r'jurisdiction',
        muckrock.jurisdiction.viewsets.JurisdictionViewSet,
        'api-jurisdiction')
router.register(r'agency',
        muckrock.agency.views.AgencyViewSet,
        'api-agency')
router.register(r'foia',
        muckrock.foia.viewsets.FOIARequestViewSet,
        'api-foia')
router.register(r'exemption',
        muckrock.jurisdiction.viewsets.ExemptionViewSet,
        'api-exemption')
router.register(r'question',
        muckrock.qanda.views.QuestionViewSet,
        'api-question')
router.register(r'statistics',
        muckrock.accounts.views.StatisticsViewSet,
        'api-statistics')
router.register(r'communication',
        muckrock.foia.viewsets.FOIACommunicationViewSet,
        'api-communication')
router.register(r'user',
        muckrock.accounts.views.UserViewSet,
        'api-user')
router.register(r'news',
        muckrock.news.views.ArticleViewSet,
        'api-news')
router.register(r'task',
        muckrock.task.viewsets.TaskViewSet,
        'api-task')
router.register(r'orphantask',
        muckrock.task.viewsets.OrphanTaskViewSet,
        'api-orphantask')
router.register(r'snailmailtask',
        muckrock.task.viewsets.SnailMailTaskViewSet,
        'api-snailmailtask')
router.register(r'rejectedemailtask',
        muckrock.task.viewsets.RejectedEmailTaskViewSet,
        'api-rejectedemailtask')
router.register(r'staleagencytask',
        muckrock.task.viewsets.StaleAgencyTaskViewSet,
        'api-staleagencytask')
router.register(r'flaggedtask',
        muckrock.task.viewsets.FlaggedTaskViewSet,
        'api-flaggedtask')
router.register(r'newagencytask',
        muckrock.task.viewsets.NewAgencyTaskViewSet,
        'api-newagencytask')
router.register(r'responsetask',
        muckrock.task.viewsets.ResponseTaskViewSet,
        'api-responsetask')

urlpatterns = [
    url(r'^$', views.homepage, name='index'),
    url(r'^reset_cache/$', views.reset_homepage_cache, name='reset-cache'),
    url(r'^accounts/', include('muckrock.accounts.urls')),
    url(r'^foi/', include('muckrock.foia.urls')),
    url(r'^news/', include('muckrock.news.urls')),
    url(r'^newsletter/$', views.NewsletterSignupView.as_view(), name='newsletter'),
    url(r'^mailgun/', include('muckrock.mailgun.urls')),
    url(r'^agency/', include('muckrock.agency.urls')),
    url(r'^place/', include(muckrock.jurisdiction.urls.urlpatterns)),
    url(r'^jurisdiction/',
        include(muckrock.jurisdiction.urls.old_urlpatterns)),
    url(r'^questions/', include('muckrock.qanda.urls')),
    url(r'^crowdfund/', include('muckrock.crowdfund.urls')),
    url(r'^task/', include('muckrock.task.urls')),
    url(r'^tags/', include('muckrock.tags.urls')),
    url(r'^organization/', include('muckrock.organization.urls')),
    url(r'^project/', include('muckrock.project.urls')),
    url(r'^map/', include('muckrock.map.urls')),
    url(r'^fine-uploader/', include('muckrock.fine_uploader.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/$', views.SearchView.as_view(), name='search'),
    url(r'^settings/', include(dbsettings.urls)),
    url(r'^api_v1/', include(router.urls)),
    url(r'^api_v1/token-auth/', obtain_auth_token, name='api-token-auth'),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^robots\.txt$', include('robots.urls')),
    url(r'^favicon.ico$', RedirectView.as_view(
        url=settings.STATIC_URL + 'icons/favicon.ico')),
    url(r'^sitemap\.xml$', django.contrib.sitemaps.views.index, {'sitemaps': sitemaps}),
    url(
        r'^sitemap-(?P<section>.+)\.xml$',
        django.contrib.sitemaps.views.sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    url(r'^news-sitemaps/', include('news_sitemaps.urls')),
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^donate/$', views.DonationFormView.as_view(), name='donate'),
    url(r'^donate/thanks/$', views.DonationThanksView.as_view(), name='donate-thanks'),
    url(r'^landing/$', views.LandingView.as_view(), name='landing'),
    url(r'^hijack/', include('hijack.urls')),
    ]


if settings.DEBUG:
    urlpatterns += [
        url(
            r'^media/(?P<path>.*)$',
            static.serve,
            {'document_root': settings.MEDIA_ROOT}
        ),
        url(r'^500/$', TemplateView.as_view(template_name='500.html')),
        url(r'^404/$', TemplateView.as_view(template_name='404.html')),
        ]
