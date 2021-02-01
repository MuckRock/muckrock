"""Constants for the Crowdsourcing app"""

# Standard Library
import re

DOCUMENT_URL_RE = re.compile(
    r"https?://(www|beta)[.]documentcloud[.]org/documents/(?P<doc_id>[0-9A-Za-z-]+)/?"
)
PROJECT_URL_RE = re.compile(
    r"https?://(www|beta)[.]documentcloud[.]org/projects/(?P<proj_id>[0-9]+)/?"
)
