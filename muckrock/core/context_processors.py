"""
Site-wide context processors
"""

# Django
from django.conf import settings as django_settings
from django.utils.functional import SimpleLazyObject

# Standard Library
import hashlib

# Third Party
from constance import config

# MuckRock
# Local
from muckrock.core.models import HomePage


def domain(request):
    """Add the domain to the context for constructing absolute urls."""
    return {"domain": request.get_host()}


def settings(request):
    """Add settings to the context"""
    return {"settings": django_settings}


def google_analytics(request):
    """
    Retrieve and delete any analytics session data and send it to the template
    """
    return {
        "ga": request.session.pop("ga", None),
        "donated": request.session.pop("donated", 0),
    }


def mixpanel(request):
    """
    Retrieve and delete any mixpanel analytics session data and send it to the template
    """
    return {
        "mp_events": SimpleLazyObject(lambda: request.session.pop("mp_events", [])),
        "mp_alias": SimpleLazyObject(lambda: request.session.pop("mp_alias", False)),
        "mp_charge": SimpleLazyObject(lambda: request.session.pop("mp_charge", 0)),
        "mp_token": django_settings.MIXPANEL_TOKEN,
    }


def cache_timeout(request):
    """Cache timeout settings"""
    return {"cache_timeout": django_settings.DEFAULT_CACHE_TIMEOUT}


def givebutter_campaign(request):
    """Add GiveButter campaign ID to the context"""
    return {"givebutter_campaign_id": config.GIVEBUTTER_CAMPAIGN_ID}


def banner(request):
    """Add banner message and hash to the context"""
    homepage = HomePage.load()
    banner_message = homepage.banner_message

    # Generate MD5 hash of the banner message for tracking dismissals
    banner_hash = ""
    if banner_message:
        banner_hash = hashlib.md5(banner_message.encode("utf-8")).hexdigest()

    # Check if user has dismissed this banner in their session
    dismissed_banners = request.session.get("dismissed_banners", [])
    show_banner = bool(banner_message and banner_hash not in dismissed_banners)

    return {
        "banner_message": banner_message,
        "banner_message_hash": banner_hash,
        "show_banner": show_banner,
    }
