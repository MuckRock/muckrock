"""
URLs for tag pages
"""
from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.TagListView.as_view(), name='tag-list'),
    url(r'^(?P<slug>[\w-]+)/$', views.TagDetailView.as_view(), name='tag-detail'),
)
