from django.conf.urls import patterns, url

from muckrock.search import views

urlpatterns = patterns('',
    url(r'^$',
        views.SearchView.as_view(),
        name='search'),
    url(r'^foi/$',
        views.FOIASearchView.as_view(),
        name='search-foia'),
)
