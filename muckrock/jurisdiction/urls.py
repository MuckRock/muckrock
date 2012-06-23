"""
URL mappings for the jurisdiction application
"""

from django.conf.urls.defaults import patterns, url

from jurisdiction import views

jurisdiction_url = r'(?P<slug>[\w\d_-]+)/(?P<idx>\d+)'

urlpatterns = patterns('',
    url(r'^view/%s/$' % jurisdiction_url, views.detail, name='jurisdiction-detail'),
    url(r'^flag/%s/$' % jurisdiction_url, views.flag, name='jurisdiction-flag'),
)

