"""
URL mappings for muckrock project
"""

from django.conf.urls.defaults import patterns, include
from django.contrib import admin

from django.views.generic.simple import direct_to_template
from django.contrib.auth.views import login, logout, password_change, password_change_done, \
    password_reset, password_reset_done, password_reset_confirm, password_reset_complete

from views import register, update
import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'home.html'}),

    (r'^accounts/login/$',             login),
    (r'^accounts/logout/$',            logout),
    (r'^accounts/profile/$',           direct_to_template,
        {'template': 'registration/profile.html'}),
    (r'^accounts/register/$',          register),
    (r'^accounts/update/$',            update),
    (r'^accounts/change_pw/$',         password_change),
    (r'^accounts/change_pw_done/$',    password_change_done),
    (r'^accounts/reset_pw/$',          password_reset),
    (r'^accounts/reset_pw_done/$',     password_reset_done),
    (r'^accounts/reset_pw_complete/$', password_reset_complete),
    (r'^accounts/reset_pw/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',  password_reset_confirm),

    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '/home/mitch/documents/work/muckrock/src/muckrock/static'}),
    )
