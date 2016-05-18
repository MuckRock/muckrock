"""
Site-wide context processors
"""
from django.conf import settings

def site_root(request):
    """Add the site root to the context for constructing absolute urls."""
    # pylint: disable=unused-argument
    return {'SITE_ROOT': settings.SITE_ROOT}

def google_analytics(request):
    """
    Retrieve and delete any google analytics session data and send it to the template
    """
    return {'ga': request.session.pop('ga', None)}
