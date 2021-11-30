"""
URL mappings for the Agency application
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.agency import views
from muckrock.core.views import jurisdiction

# pylint: disable=bad-whitespace

agency_url = (
    r"(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)"
)
old_agency_url = r"(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)"

urlpatterns = [
    re_path(r"^$", views.AgencyList.as_view(), name="agency-list"),
    re_path(r"^%s/$" % agency_url, views.detail, name="agency-detail"),
    re_path(r"^(?P<action>\w+)/%s/$" % old_agency_url, views.redirect_old),
    re_path(
        r"^(?P<jurisdiction>[\w\d_-]+)-(?P<idx>\d+)/$",
        jurisdiction,
        name="agency-jurisdiction",
    ),
    re_path(r"^%s/flag/$" % agency_url, views.redirect_flag, name="agency-flag"),
    re_path(r"^boilerplate/$", views.boilerplate, name="agency-boilerplate"),
    re_path(
        r"^contact-info/(?P<idx>\d+)/$", views.contact_info, name="agency-contact-info"
    ),
    re_path(r"^merge/$", views.MergeAgency.as_view(), name="agency-merge"),
    re_path(
        r"^agency-autocomplete/$",
        views.AgencyAutocomplete.as_view(),
        name="agency-autocomplete",
    ),
    re_path(
        r"^agency-composer-autocomplete/$",
        views.AgencyComposerAutocomplete.as_view(),
        name="agency-composer-autocomplete",
    ),
    re_path(r"^import/$", views.MassImportAgency.as_view(), name="agency-mass-import"),
]
