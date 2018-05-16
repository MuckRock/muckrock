"""
Site-wide context processors
"""
# Django
from django.conf import settings


def domain(request):
    """Add the domain to the context for constructing absolute urls."""
    return {'domain': request.get_host()}


def google_analytics(request):
    """
    Retrieve and delete any analytics session data and send it to the template
    """
    return {
        'ga': request.session.pop('ga', None),
        'donated': request.session.pop('donated', 0),
    }


def mixpanel(request):
    """
    Retrieve and delete any mixpanel analytics session data and send it to the template
    """
    return {
        'mp_events': request.session.pop('mp_events', []),
        'mp_alias': request.session.pop('mp_alias', False),
        'mp_charge': request.session.pop('mp_charge', 0),
        'mp_token': settings.MIXPANEL_TOKEN,
    }


def cache_timeout(request):
    """Cache timeout settings"""
    # pylint: disable=unused-argument
    return {'cache_timeout': settings.DEFAULT_CACHE_TIMEOUT}
