"""
URL mappings for the Agency application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from agency import views
from muckrock.views import jurisdiction

agency_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<idx>\d+)-(?P<slug>[\w\d_-]+)'
old_agency_url = r'(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns('',
    # XXX need a root, list all agencies?
    url(r'^%s/$' % agency_url,        redirect_to, {'url': 'view'}, name='agency-default'),
    url(r'^%s/view/$' % agency_url,   views.detail, name='agency-detail'),
    url(r'^%s/update/$' % agency_url, views.update, name='agency-update'),
    url(r'^%s/flag/$' % agency_url,   views.flag, name='agency-flag'),
    url(r'^(?P<jurisdiction>[\w\d_-]+)/$',
                                      jurisdiction, name='agency-jurisdiction'),

    # old urls for redirects
    url(r'^view/%s/$' % old_agency_url,
        redirect_to, {'url': '/agency/%(jurisdiction)s/%(idx)s-%(slug)s/view/'}),
    url(r'^update/%s/$' % old_agency_url,
        redirect_to, {'url': '/agency/%(jurisdiction)s/%(idx)s-%(slug)s/update/'}),
    url(r'^flag/%s/$' % old_agency_url,
        redirect_to, {'url': '/agency/%(jurisdiction)s/%(idx)s-%(slug)s/flag/'}),
)
