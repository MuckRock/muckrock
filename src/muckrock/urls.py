"""
URL mappings for muckrock project
"""

# pylint: disable-msg=W0611
# these are called dynmically
from django.conf.urls.defaults import handler404, handler500
# pylint: enable-msg=W0611
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.views.decorators.csrf import csrf_exempt

import haystack.urls
from django_xmlrpc.views import handle_xmlrpc

import accounts.urls, foia.urls, news.urls, rodeo.urls
import settings
import views
from foia.sitemap import FoiaSitemap
from news.sitemap import ArticleSitemap

admin.autodiscover()

sitemaps = {'FOIA': FoiaSitemap, 'News': ArticleSitemap}

urlpatterns = patterns('',
    url(r'^$', views.front_page, name='index'),
    url(r'^accounts/', include(accounts.urls)),
    url(r'^foi/', include(foia.urls)),
    url(r'^foi/', include(rodeo.urls)),
    url(r'^news/', include(news.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', include(haystack.urls)),
    url(r'^xmlrpc/$', csrf_exempt(handle_xmlrpc), name='xmlrpc'),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
