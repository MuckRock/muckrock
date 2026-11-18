"""
Lob API access through lob-python
"""

# Django
from django.conf import settings

# Standard Library
import json

# Third Party
import lob_python

TIMEOUT = (10, 120)


def call(api_class, method, *args):
    """Call a lob-python API method, returning Lob's response as a dict

    Raises lob_python.ApiException when Lob returns an error.
    """
    config = lob_python.Configuration(username=settings.LOB_SECRET_KEY)
    with lob_python.ApiClient(config) as client:
        # Lob has already acted by the time the response is parsed, so skip
        # lob-python's response models: a parse error would read as a rejection.
        response = getattr(api_class(client), method)(
            *args, _preload_content=False, _request_timeout=TIMEOUT
        )
    return json.loads(response.data)


def error_message(exc):
    """Lob's error message from an ApiException, or the HTTP reason"""
    try:
        return json.loads(exc.body)["error"]["message"]
    except (TypeError, ValueError, KeyError):
        return str(exc.reason)
