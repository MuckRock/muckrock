"""Constants for the Crowdsourcing app"""

# Standard Library
import re

DOCUMENT_URL_RE = re.compile(
    r'https?://www[.]documentcloud[.]org/documents/'
    r'(?P<doc_id>[0-9A-Za-z-]+)[.]html'
)
PROJECT_URL_RE = re.compile(
    r'https?://www[.]documentcloud[.]org/projects/'
    r'(?P<proj_id>[0-9A-Za-z-]+)[.]html'
)
