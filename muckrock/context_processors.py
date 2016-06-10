"""
Site-wide context processors
"""
from django.contrib.sites.models import Site

def domain(request):
    """Add the domain to the context for constructing absolute urls."""
    # pylint: disable=unused-argument
    current_site = Site.objects.get_current()
    return {'domain': current_site.domain}

def google_analytics(request):
    """
    Retrieve and delete any google analytics session data and send it to the template
    """
    return {'ga': request.session.pop('ga', None)}
