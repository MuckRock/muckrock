"""
URL mappings for the Agency application
"""

from django.conf.urls import patterns, url

from muckrock.agency import views
from muckrock.views import jurisdiction

# pylint: disable=bad-whitespace

agency_url = r'(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)'
old_agency_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns(
    '',
    url(r'^$', views.AgencyList.as_view(), name='agency-list'),
    url(r'^%s/$' % agency_url, views.detail, name='agency-detail'),
    url(r'^(?P<action>\w+)/%s/$' % old_agency_url, views.redirect_old),
    url(
        r'^(?P<jurisdiction>[\w\d_-]+)-(?P<idx>\d+)/$',
        jurisdiction,
        name='agency-jurisdiction'
    ),
    url(
        r'^%s/flag/$' % agency_url,
        views.redirect_flag,
    ),
)
