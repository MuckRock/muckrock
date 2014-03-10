"""
URL mappings for muckrock project
"""

# pylint: disable=W0611
# these are called dynmically
from django.conf.urls.defaults import handler404
from views import handler500
# pylint: enable=W0611
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.views.decorators.csrf import csrf_exempt

from django_xmlrpc.views import handle_xmlrpc
from rest_framework.routers import DefaultRouter
import autocomplete_light
import haystack.urls, dbsettings.urls

autocomplete_light.autodiscover()

import muckrock.accounts.urls, muckrock.foia.urls, muckrock.news.urls, muckrock.agency.urls, \
       muckrock.jurisdiction.urls, muckrock.mailgun.urls, muckrock.qanda.urls, \
       muckrock.crowdfund.urls
import muckrock.agency.views, muckrock.foia.viewsets, muckrock.jurisdiction.views
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
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', include(haystack.urls)),
    url(r'^settings/', include(dbsettings.urls)),
    url(r'^api_v1/', include(router.urls)),
    url(r'^api_v1/token-auth/', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^xmlrpc/$', csrf_exempt(handle_xmlrpc), name='xmlrpc'),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    url(r'^blog/(?P<path>.*)$', views.blog, name='blog'),
)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
