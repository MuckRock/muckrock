"""
URL mappings for the Organization application
"""

from django.conf.urls import patterns, url

from muckrock.organization import views

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.List.as_view(),
        name='org-index'
    ),
    url(
        r'^create/$',
        views.create_organization,
        name='org-create'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)/$',
        views.Detail.as_view(),
        name='org-detail'
    ),
    url(
        r'^(?P<slug>[\w\d_-]+)/delete/$',
        views.delete_organization,
        name='org-delete'
    ),
)
