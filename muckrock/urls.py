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

import accounts.urls, foia.urls, news.urls, rodeo.urls, agency.urls, jurisdiction.urls, mailgun.urls
import haystack.urls, dbsettings.urls
import settings
import views
from foia.sitemap import FoiaSitemap
from news.sitemap import ArticleSitemap

admin.autodiscover()
admin.site.index_template = 'admin/custom_index.html'

sitemaps = {'FOIA': FoiaSitemap, 'News': ArticleSitemap}

urlpatterns = patterns('',
    url(r'^$', views.front_page, name='index'),
    url(r'^accounts/', include(accounts.urls)),
    url(r'^foi/', include(foia.urls)),
    url(r'^foi/', include(rodeo.urls)),
    url(r'^news/', include(news.urls)),
    url(r'^mailgun/', include(mailgun.urls)),
    url(r'^agency/', include(agency.urls)),
    url(r'^jurisdiction/', include(jurisdiction.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', include(haystack.urls)),
    url(r'^settings/', include(dbsettings.urls)),
    url(r'^xmlrpc/$', csrf_exempt(handle_xmlrpc), name='xmlrpc'),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )
