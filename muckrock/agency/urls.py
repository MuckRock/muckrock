"""
URL mappings for the Agency application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.agency import views
from muckrock.core.views import jurisdiction

# pylint: disable=bad-whitespace

agency_url = (
    r"(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)"
)
old_agency_url = r"(?P<jurisdiction>[\w\d_-]+)/(?P<slug>[\w\d_-]+)/(?P<idx>\d+)"

urlpatterns = [
    url(r"^$", views.AgencyList.as_view(), name="agency-list"),
    url(r"^%s/$" % agency_url, views.detail, name="agency-detail"),
    url(r"^(?P<action>\w+)/%s/$" % old_agency_url, views.redirect_old),
    url(
        r"^(?P<jurisdiction>[\w\d_-]+)-(?P<idx>\d+)/$",
        jurisdiction,
        name="agency-jurisdiction",
    ),
    url(r"^%s/flag/$" % agency_url, views.redirect_flag, name="agency-flag"),
    url(r"^boilerplate/$", views.boilerplate, name="agency-boilerplate"),
    url(
        r"^contact-info/(?P<idx>\d+)/$", views.contact_info, name="agency-contact-info"
    ),
    url(r"^merge/$", views.MergeAgency.as_view(), name="agency-merge"),
    url(
        r"^agency-autocomplete/$",
        views.AgencyAutocomplete.as_view(),
        name="agency-autocomplete",
    ),
    url(
        r"^agency-composer-autocomplete/$",
        views.AgencyComposerAutocomplete.as_view(),
        name="agency-composer-autocomplete",
    ),
    url(r"^import/$", views.MassImportAgency.as_view(), name="agency-mass-import"),
]
