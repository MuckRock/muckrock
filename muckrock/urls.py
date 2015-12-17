"""
URL mappings for muckrock project
"""

# pylint: disable=unused-import
# these are called dynmically
from django.conf.urls import handler404
from views import handler500
# pylint: enable=unused-import
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView

from django_xmlrpc.views import handle_xmlrpc
from rest_framework.routers import DefaultRouter
import dbsettings.urls

import muckrock.accounts.urls, muckrock.foia.urls, muckrock.news.urls, muckrock.agency.urls, \
       muckrock.jurisdiction.urls, muckrock.mailgun.urls, muckrock.qanda.urls, \
       muckrock.crowdfund.urls, muckrock.organization.urls, muckrock.task.urls, \
       muckrock.project.urls, muckrock.tags.urls
import muckrock.agency.views, muckrock.foia.viewsets, muckrock.jurisdiction.views, \
       muckrock.accounts.views, muckrock.task.viewsets
import muckrock.settings as settings
import muckrock.views as views
from muckrock.agency.sitemap import AgencySitemap
from muckrock.foia.sitemap import FoiaSitemap
from muckrock.jurisdiction.sitemap import JurisdictionSitemap
from muckrock.news.sitemap import ArticleSitemap

admin.site.index_template = 'admin/custom_index.html'

sitemaps = {'FOIA': FoiaSitemap, 'News': ArticleSitemap,
            'Agency': AgencySitemap, 'Jurisdiction': JurisdictionSitemap}

router = DefaultRouter()
router.register(r'jurisdiction',
        muckrock.jurisdiction.views.JurisdictionViewSet,
        'api-jurisdiction')
router.register(r'agency',
        muckrock.agency.views.AgencyViewSet,
        'api-agency')
router.register(r'foia',
        muckrock.foia.viewsets.FOIARequestViewSet,
        'api-foia')
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

urlpatterns = patterns(
    '',
    url(r'^$', views.homepage, name='index'),
    url(r'^accounts/', include(muckrock.accounts.urls)),
    url(r'^foi/', include(muckrock.foia.urls)),
    url(r'^news/', include(muckrock.news.urls)),
    url(r'^mailgun/', include(muckrock.mailgun.urls)),
    url(r'^agency/', include(muckrock.agency.urls)),
    url(r'^place/', include(muckrock.jurisdiction.urls.urlpatterns)),
    url(r'^jurisdiction/', include(muckrock.jurisdiction.urls.old_urlpatterns)),
    url(r'^questions/', include(muckrock.qanda.urls)),
    url(r'^crowdfund/', include(muckrock.crowdfund.urls)),
    url(r'^task/', include(muckrock.task.urls)),
    url(r'^tags/', include(muckrock.tags.urls)),
    url(r'^organization/', include(muckrock.organization.urls)),
    url(r'^project/', include(muckrock.project.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/$', views.MRSearchView(), name='search'),
    url(r'^settings/', include(dbsettings.urls)),
    url(r'^api_v1/', include(router.urls)),
    url(r'^api_v1/token-auth/', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^api_doc/', include('rest_framework_swagger.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^activity/', include('actstream.urls')),
    url(r'^xmlrpc/$', csrf_exempt(handle_xmlrpc), name='xmlrpc'),
    url(r'^blog/(?P<path>.*)$', views.blog, name='blog'),
    url(r'^robots\.txt$', include('robots.urls')),
    url(r'^favicon.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico')),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.index', {'sitemaps': sitemaps}),
    url(
        r'^sitemap-(?P<section>.+)\.xml$',
        'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}
    ),
    url(r'^news-sitemaps/', include('news_sitemaps.urls')),

)

import debug_toolbar
urlpatterns += patterns('',
    url(r'^__debug__/', include(debug_toolbar.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(
            r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}
        ),
    )
