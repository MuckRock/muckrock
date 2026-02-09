"""Constants for the Crowdsourcing app"""

# Standard Library
import re

BASE = r"https?://(www|beta|staging)\.documentcloud\.org"

DOCUMENT_URL_RE = re.compile(rf"{BASE}/documents/(?P<doc_id>[0-9A-Za-z-]+)/?")
PROJECT_URL_RE = re.compile(rf"{BASE}/projects/(?P<proj_id>[0-9]+)/?")
