"""
URL mappings for muckrock project
"""

# pylint: disable=W0611
# these are called dynmically
from django.conf.urls import handler404
from views import handler500
# pylint: enable=W0611
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView

from django_xmlrpc.views import handle_xmlrpc
from rest_framework.routers import DefaultRouter
import autocomplete_light
import haystack.urls, dbsettings.urls

autocomplete_light.autodiscover()

import muckrock.accounts.urls, muckrock.foia.urls, muckrock.news.urls, muckrock.agency.urls, \
       muckrock.jurisdiction.urls, muckrock.mailgun.urls, muckrock.qanda.urls, \
       muckrock.crowdfund.urls, muckrock.organization.urls
import muckrock.agency.views, muckrock.foia.viewsets, muckrock.jurisdiction.views, \
       muckrock.accounts.views, muckrock.sidebar.viewsets
import muckrock.settings as settings
import muckrock.views as views
from muckrock.foia.sitemap import FoiaSitemap
from muckrock.news.sitemap import ArticleSitemap

admin.autodiscover()
admin.site.index_template = 'admin/custom_index.html'

sitemaps = {'FOIA': FoiaSitemap, 'News': ArticleSitemap}

router = DefaultRouter()
router.register(r'jurisdiction', muckrock.jurisdiction.views.JurisdictionViewSet)
router.register(r'agency', muckrock.agency.views.AgencyViewSet)
router.register(r'foia', muckrock.foia.viewsets.FOIARequestViewSet)
router.register(r'question', muckrock.qanda.views.QuestionViewSet)
router.register(r'statistics', muckrock.accounts.views.StatisticsViewSet)
router.register(r'communication', muckrock.foia.viewsets.FOIACommunicationViewSet)
router.register(r'user', muckrock.accounts.views.UserViewSet)
router.register(r'news', muckrock.news.views.ArticleViewSet)
router.register(r'sidebar', muckrock.sidebar.viewsets.SidebarViewSet)

urlpatterns = patterns('',
    url(r'^$', views.front_page, name='index'),
    url(r'^accounts/', include(muckrock.accounts.urls)),
    url(r'^foi/', include(muckrock.foia.urls)),
    url(r'^news/', include(muckrock.news.urls)),
    url(r'^mailgun/', include(muckrock.mailgun.urls)),
    url(r'^agency/', include(muckrock.agency.urls)),
    url(r'^place/', include(muckrock.jurisdiction.urls.urlpatterns)),
    url(r'^jurisdiction/', include(muckrock.jurisdiction.urls.old_urlpatterns)),
    url(r'^questions/', include(muckrock.qanda.urls)),
    url(r'^crowdfund/', include(muckrock.crowdfund.urls)),
    url(r'^organization/', include(muckrock.organization.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', include(haystack.urls)),
    url(r'^settings/', include(dbsettings.urls)),
    url(r'^api_v1/', include(router.urls)),
    url(r'^api_v1/token-auth/', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^api_doc/', include('rest_framework_swagger.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^xmlrpc/$', csrf_exempt(handle_xmlrpc), name='xmlrpc'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.index', {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}),
    url(r'^blog/(?P<path>.*)$', views.blog, name='blog'),
    url(r'^robots\.txt$', include('robots.urls')),
    url(r'^favicon.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico')),
)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
