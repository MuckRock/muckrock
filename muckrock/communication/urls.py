"""
URL mappings for the communicaiton app
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.communication import views

urlpatterns = [
    re_path(
        r"emailaddress/(?P<idx>\d+)/$",
        views.EmailDetailView.as_view(),
        name="email-detail",
    ),
    re_path(
        r"phonenumber/(?P<idx>\d+)/$",
        views.PhoneDetailView.as_view(),
        name="phone-detail",
    ),
    re_path(r"checks/$", views.CheckListView.as_view(), name="check-list"),
    re_path(
        r"^email-autocomplete/$",
        views.EmailAutocomplete.as_view(),
        name="email-autocomplete",
    ),
    re_path(
        r"^fax-autocomplete/$", views.FaxAutocomplete.as_view(), name="fax-autocomplete"
    ),
    re_path(
        r"^phone-autocomplete/$",
        views.PhoneNumberAutocomplete.as_view(),
        name="phone-autocomplete",
    ),
    re_path(
        r"^email-fax-autocomplete/$",
        views.EmailOrFaxAutocomplete.as_view(),
        name="email-fax-autocomplete",
    ),
]
