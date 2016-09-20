"""
URL mappings for the jurisdiction application
"""

from django.conf.urls import patterns, url

from muckrock.jurisdiction import views
from muckrock.views import jurisdiction

jur_url = r'(?P<fed_slug>[\w\d_-]+)(?:/(?P<state_slug>[\w\d_-]+))?(?:/(?P<local_slug>[\w\d_-]+))?'
old_jur_url = r'(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns(
    '',
    url(r'^$',
        views.List.as_view(),
        name='jurisdiction-list'
    ),
    url(r'^%s/flag/$' % jur_url,
        views.redirect_flag
    ),
    url(r'^%s/exemption/(?P<slug>[\w-]+)-(?P<pk>\d+)/$' % jur_url,
        views.ExemptionDetailView.as_view(),
        name='exemption-detail',
    ),
    url(r'^%s/$' % jur_url,
        views.detail,
        name='jurisdiction-detail'
    ),
)

# old url patterns go under jurisdictions, new ones switched to places
old_urlpatterns = patterns(
    '',
    url(r'^view/%s/$' % old_jur_url, jurisdiction),
    url(r'^flag/%s/$' % old_jur_url, jurisdiction, {'view': 'flag'}),
)



