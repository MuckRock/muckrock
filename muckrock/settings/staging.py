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

INSTALLED_APPS += ("bandit",)

BANDIT_EMAIL = os.environ.get("BANDIT_EMAIL", "staging@muckrock.com")
BANDIT_WHITELIST = [
    e.strip() for e in os.environ.get("BANDIT_WHITELIST", "").split(",") if e.strip()
]
# I was being redirected to SSL locally so I disabled
SECURE_SSL_REDIRECT = False

# got some warning locally about compression, this can probably be killed after you sort out the prod/staging/local stuff
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False


class HijackMailgunBackend(HijackBackendMixin, MailgunBackend):
    """This backend hijacks all emails and sends them via Mailgun"""


EMAIL_BACKEND = "muckrock.settings.staging.HijackMailgunBackend"

# set proxy for static outgoing IP address, so we can cross
# white list muckrock and squarelet staging sites
os.environ["http_proxy"] = os.environ.get("FIXIE_URL", "")
os.environ["https_proxy"] = os.environ.get("FIXIE_URL", "")

SCOUT_NAME = "MuckRock Staging"

DEBUG = True
