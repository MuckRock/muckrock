"""
URL mappings for muckrock project
"""

# pylint: disable-msg=W0611
# these are called dynmically
from django.conf.urls.defaults import handler404, handler500
# pylint: enable-msg=W0611
from django.conf.urls.defaults import patterns, include
from django.contrib import admin
from django.views.generic.simple import direct_to_template

import muckrock.accounts.urls, muckrock.foia.urls, muckrock.news.urls
import muckrock.settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'home.html'}),
    (r'^accounts/', include(muckrock.accounts.urls)),
    (r'^foia/', include(muckrock.foia.urls)),
    (r'^news/', include(muckrock.news.urls)),
    (r'^admin/', include(admin.site.urls)),
)

if muckrock.settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/mitch/documents/work/muckrock/src/muckrock/static'}),
    )
