"""
URL mappings for muckrock project
"""

# pylint: disable-msg=W0611
# these are called dynmically
from django.conf.urls.defaults import handler404, handler500
# pylint: enable-msg=W0611
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic.date_based import archive_index

import muckrock.accounts.urls, muckrock.foia.urls, muckrock.news.urls
import muckrock.settings
from muckrock.news.models import Article

admin.autodiscover()

article_args = {'queryset': Article.objects.get_published(), 'date_field': 'pub_date',
                'allow_empty': True, 'num_latest': 5}

urlpatterns = patterns('',
    url(r'^$', archive_index, article_args, name='index'),
    url(r'^accounts/', include(muckrock.accounts.urls)),
    url(r'^foia/', include(muckrock.foia.urls)),
    url(r'^news/', include(muckrock.news.urls)),
    url(r'^admin/', include(admin.site.urls)),
)

if muckrock.settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/mitch/documents/work/muckrock/src/muckrock/static'}),
        (r'^user_media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/mitch/documents/work/muckrock/src/muckrock/user_media'}),
    )
