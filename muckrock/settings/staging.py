"""
Settings used when deployed to the staging server
Imports from the heroku settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# Third Party
from bandit.backends.base import HijackBackendMixin
from django_mailgun import MailgunBackend

# MuckRock
from muckrock.settings.heroku import *

INSTALLED_APPS += (
    "bandit",
    "silk",
)

BANDIT_EMAIL = os.environ.get("BANDIT_EMAIL", "staging@muckrock.com")
BANDIT_WHITELIST = [
    e.strip() for e in os.environ.get("BANDIT_WHITELIST", "").split(",") if e.strip()
]


class HijackMailgunBackend(HijackBackendMixin, MailgunBackend):
    """This backend hijacks all emails and sends them via Mailgun"""


EMAIL_BACKEND = "muckrock.settings.staging.HijackMailgunBackend"

# set proxy for static outgoing IP address, so we can cross
# white list muckrock and squarelet staging sites
os.environ["http_proxy"] = os.environ.get("FIXIE_URL", "")
os.environ["https_proxy"] = os.environ.get("FIXIE_URL", "")

SCOUT_NAME = "MuckRock Staging"

DEBUG = True

MIDDLEWARE = ("silk.middleware.SilkyMiddleware",) + MIDDLEWARE
