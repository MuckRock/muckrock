"""
URL mappings for the jurisdiction application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to

from jurisdiction import views
from muckrock.views import jurisdiction

jur_url = r'(?P<fed_slug>[\w\d_-]+)(?:/(?P<state_slug>[\w\d_-]+))?(?:/(?P<local_slug>[\w\d_-]+))?'
old_jur_url = r'(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns('',
    # XXX need a root, list all jurisdictions?
    url(r'^%s/$' % jur_url,      redirect_to, {'url': 'view'}, name='jurisdiction-default'),
    url(r'^%s/view/$' % jur_url, views.detail, name='jurisdiction-detail'),
    url(r'^%s/flag/$' % jur_url, views.flag, name='jurisdiction-flag'),

)

# old url patterns go under jurisdictions, new ones switched to places
old_urlpatterns = patterns('',
    url(r'^view/%s/$' % old_jur_url, jurisdiction),
    url(r'^flag/%s/$' % old_jur_url, jurisdiction, {'view': 'flag'}),
)

