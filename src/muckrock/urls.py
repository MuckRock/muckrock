from django.conf.urls.defaults import *
from django.contrib import admin

from django.views.generic.simple import direct_to_template
from django.contrib.auth.views import login, logout

from views import register, update
import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$',                   direct_to_template, {'template': 'home.html'}),

    (r'^accounts/login/$',    login),
    (r'^accounts/logout/$',   logout),
    (r'^accounts/profile/$',  direct_to_template, {'template': 'registration/profile.html'}),
    (r'^accounts/register/$', register),
    (r'^accounts/update/$',   update),

    (r'^admin/',              include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/mitch/documents/work/muckrock/src/muckrock/static'}),
    )
