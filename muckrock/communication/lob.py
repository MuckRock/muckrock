"""
Client for the Lob print-and-mail API
"""

# Django
from django.conf import settings

# Third Party
import requests

LOB_API = "https://api.lob.com/v1"
TIMEOUT = (10, 120)


class LobError(Exception):
    """Lob rejected the request; args[0] is Lob's error message"""


class LobTimeoutError(LobError):
    """Lob's gateway timed out, so the request may be retried"""


def _form(params):
    """Flatten nested params into the `key[subkey]` form fields Lob expects"""
    form = {}
    for key, value in params.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                form[f"{key}[{subkey}]"] = subvalue
        elif isinstance(value, bool):
            form[key] = str(value).lower()
        elif value is not None:
            form[key] = value
    return form


def _request(method, path, **kwargs):
    response = requests.request(
        method,
        f"{LOB_API}{path}",
        auth=(settings.LOB_SECRET_KEY, ""),
        timeout=TIMEOUT,
        **kwargs,
    )
    if response.status_code == 504:
        raise LobTimeoutError(response.text or response.reason)
    try:
        payload = response.json()
    except ValueError as exc:
        raise LobError(response.text or response.reason) from exc
    if not response.ok:
        raise LobError(payload.get("error", {}).get("message", response.text))
    return payload


def create_letter(file, to, from_, **params):
    """Mail a letter, returning Lob's letter object"""
    return _request(
        "POST",
        "/letters",
        data=_form({"to": to, "from": from_, **params}),
        files={"file": ("letter.pdf", file, "application/pdf")},
    )


def create_check(attachment, to, from_, **params):
    """Mail a check, returning Lob's check object"""
    return _request(
        "POST",
        "/checks",
        data=_form({"to": to, "from": from_, **params}),
        files={"attachment": ("attachment.pdf", attachment, "application/pdf")},
    )


def retrieve_check(check_id):
    """Fetch Lob's check object"""
    return _request("GET", f"/checks/{check_id}")
