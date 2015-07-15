"""
URL mappings for the Organization application
"""

from django.conf.urls import patterns, url

from muckrock.organization import views

urlpatterns = patterns(
    '',
    url(
        r'^$',
        views.OrganizationListView.as_view(),
        name='org-index'
    ),
    url(
        r'^create/$',
        views.OrganizationCreateView.as_view(),
        name='org-create'
    ),
    url(
        r'^(?P<slug>[\w-]+)/$',
        views.OrganizationDetailView.as_view(),
        name='org-detail'
    ),
    url(
        r'^(?P<slug>[\w-]+)/delete/$',
        views.delete_organization,
        name='org-delete'
    ),
    url(
        r'^(?P<slug>[\w-]+)/update/$',
        views.update_organization,
        name='org-update'
    ),
)
