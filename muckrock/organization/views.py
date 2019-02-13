"""
Views for the organization application
"""
# Django
from django.conf import settings
from django.views.generic import RedirectView


class OrganizationDetailView(RedirectView):
    """Organization detail view redirects to squarelet"""
    url = '{}/organizations/%(slug)s/'.format(settings.SQUARELET_URL)


class OrganizationListView(RedirectView):
    """Organization list view redirects to squarelet"""
    url = '{}/organizations/'.format(settings.SQUARELET_URL)
