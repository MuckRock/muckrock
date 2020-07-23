"""
URL mappings for the communicaiton app
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.communication import views

urlpatterns = [
    url(
        r"emailaddress/(?P<idx>\d+)/$",
        views.EmailDetailView.as_view(),
        name="email-detail",
    ),
    url(
        r"phonenumber/(?P<idx>\d+)/$",
        views.PhoneDetailView.as_view(),
        name="phone-detail",
    ),
    url(r"checks/$", views.CheckListView.as_view(), name="check-list"),
    url(
        r"^email-autocomplete/$",
        views.EmailAutocomplete.as_view(),
        name="email-autocomplete",
    ),
    url(
        r"^fax-autocomplete/$", views.FaxAutocomplete.as_view(), name="fax-autocomplete"
    ),
    url(
        r"^phone-autocomplete/$",
        views.PhoneNumberAutocomplete.as_view(),
        name="phone-autocomplete",
    ),
    url(
        r"^email-fax-autocomplete/$",
        views.EmailOrFaxAutocomplete.as_view(),
        name="email-fax-autocomplete",
    ),
]
