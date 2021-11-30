"""
URLs for tag pages
"""
# Django
from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.TagListView.as_view(), name="tag-list"),
    re_path(
        r"^tag-autocomplete/$", views.TagAutocomplete.as_view(), name="tag-autocomplete"
    ),
    re_path(r"^(?P<slug>[\w-]+)/$", views.TagDetailView.as_view(), name="tag-detail"),
]
