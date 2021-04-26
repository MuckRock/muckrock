"""
Washington Post setting overrides for production
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from mucrock.settings.production import *

# TODO Remove me once we've verified email sending in production
EMAIL_BACKEND = "muckrock.settings.staging.HijackMailgunBackend"
BANDIT_EMAIL = os.environ.get("BANDIT_EMAIL", "staging@muckrock.com")
BANDIT_WHITELIST = [
    e.strip() for e in os.environ.get("BANDIT_WHITELIST", "").split(",") if e.strip()
]
