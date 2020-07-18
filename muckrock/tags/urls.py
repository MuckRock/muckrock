"""
URLs for tag pages
"""
# Django
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^$", views.TagListView.as_view(), name="tag-list"),
    url(
        r"^tag-autocomplete/$", views.TagAutocomplete.as_view(), name="tag-autocomplete"
    ),
    url(r"^(?P<slug>[\w-]+)/$", views.TagDetailView.as_view(), name="tag-detail"),
]
