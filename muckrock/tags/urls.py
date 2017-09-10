"""
URLs for tag pages
"""
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.TagListView.as_view(), name='tag-list'),
    url(r'^(?P<slug>[\w-]+)/$', views.TagDetailView.as_view(), name='tag-detail'),
    ]
