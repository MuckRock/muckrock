"""
Client for the Phaxio fax API
"""

# Django
from django.conf import settings

# Third Party
import requests

PHAXIO_API = "https://api.phaxio.com/v2"
TIMEOUT = (10, 120)


def create_fax(to, files, tags, **params):
    """Queue a fax, returning Phaxio's fax ID

    `files` are (filename, content, content type) tuples. Raises
    requests.HTTPError when Phaxio rejects the fax.
    """
    data = {"to[]": to, **{f"tag[{k}]": v for k, v in tags.items()}}
    for key, value in params.items():
        if isinstance(value, bool):
            data[key] = str(value).lower()
        elif value is not None:
            data[key] = value
    # Phaxio documents `file[]` for sending several files
    file_key = "file" if len(files) == 1 else "file[]"
    response = requests.post(
        f"{PHAXIO_API}/faxes",
        auth=(settings.PHAXIO_KEY, settings.PHAXIO_SECRET),
        data=data,
        files=[(file_key, file_) for file_ in files],
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["data"]["id"]
