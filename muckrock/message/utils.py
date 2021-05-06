"""Utility functions for sending slack messages"""

# Django
from django.conf import settings


def format_user(user):
    """Format a user for inclusion in a Slack notification"""
    return "<%(url)s|%(name)s>" % {
        "url": settings.MUCKROCK_URL + user.get_absolute_url(),
        "name": user.profile.full_name,
    }


def slack_message(icon, channel, text, attachments):
    """Formats and returns data in a Slack message format."""
    return {
        "icon_emoji": icon,
        "channel": channel,
        "text": text,
        "attachments": attachments,
    }


def slack_attachment(field_title, field_value, field_short=True):
    """Formats and returns data in in the Slack attachment format."""
    return {"title": field_title, "value": field_value, "short": field_short}
