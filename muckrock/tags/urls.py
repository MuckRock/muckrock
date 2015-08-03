"""
URLs for tag pages
"""
from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.TagListView.as_view(), name='tag-list')
)
