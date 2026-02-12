"""Constants for the Crowdsourcing app"""

# Django
from django.conf import settings

# Standard Library
import re

if settings.ENV == "production":
    DOCCLOUD_BASE = r"(www\.)?documentcloud\.org"
elif settings.ENV == "staging":
    DOCCLOUD_BASE = r"(www\.)?staging\.documentcloud\.org"
else:  # dev or local
    DOCCLOUD_BASE = r"(www\.)?dev\.documentcloud\.org"

# Regexes for documents and projects
DOCUMENT_URL_RE = re.compile(
    rf"^https://{DOCCLOUD_BASE}/documents/(?P<doc_id>[0-9A-Za-z-]+)/?$"
)
PROJECT_URL_RE = re.compile(
    rf"^https://{DOCCLOUD_BASE}/projects/(?P<proj_id>[0-9A-Za-z-]+)/?$"
)
