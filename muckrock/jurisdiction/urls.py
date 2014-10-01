"""
URL mappings for the jurisdiction application
"""

from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from muckrock.jurisdiction import views
from muckrock.views import jurisdiction

# pylint: disable=bad-whitespace

jur_url = r'(?P<fed_slug>[\w\d_-]+)(?:/(?P<state_slug>[\w\d_-]+))?(?:/(?P<local_slug>[\w\d_-]+))?'
old_jur_url = r'(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns('',
    url(r'^$',                   views.list_, name='jurisdiction-list'),
    url(r'^%s/$' % jur_url,      views.detail, name='jurisdiction-detail'),
    url(r'^%s/flag/$' % jur_url, RedirectView.as_view(url='/%(jur_url)s/'), name='jurisdiction-flag'),
)

# old url patterns go under jurisdictions, new ones switched to places
old_urlpatterns = patterns('',
    url(r'^view/%s/$' % old_jur_url, jurisdiction),
    url(r'^flag/%s/$' % old_jur_url, jurisdiction, {'view': 'flag'}),
)



