"""
Settings used when deployed to the staging server
Imports from the heroku settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# Third Party
from anymail.backends.mailgun import EmailBackend
from bandit.backends.base import HijackBackendMixin

# MuckRock
from muckrock.settings.heroku import *

INSTALLED_APPS += ("bandit",)

BANDIT_EMAIL = os.environ.get("BANDIT_EMAIL", "staging@muckrock.com")
BANDIT_WHITELIST = [
    e.strip() for e in os.environ.get("BANDIT_WHITELIST", "").split(",") if e.strip()
]

SECURE_SSL_REDIRECT = True


class HijackMailgunBackend(HijackBackendMixin, EmailBackend):
    """This backend hijacks all emails and sends them via Mailgun"""


EMAIL_BACKEND = "muckrock.settings.staging.HijackMailgunBackend"

# set proxy for static outgoing IP address, so we can cross
# white list muckrock and squarelet staging sites
os.environ["http_proxy"] = os.environ.get("FIXIE_URL", "")
os.environ["https_proxy"] = os.environ.get("FIXIE_URL", "")

SCOUT_NAME = "MuckRock Staging"

# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
ANYMAIL = {
    "MAILGUN_API_KEY": MAILGUN_ACCESS_KEY,
    "MAILGUN_SENDER_DOMAIN": MAILGUN_SERVER_NAME,
    "MAILGUN_API_URL": MAILGUN_API_URL,
}
