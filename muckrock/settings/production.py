"""
Settings used when deployed to the production server
Imports from the heroku settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# Standard Library
import logging
# Standard
import os

# Third Party
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# MuckRock
from muckrock.settings.heroku import *

# Security
SECURE_HSTS_SECONDS = 31536000  # one year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_FRAME_DENY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

PREPEND_WWW = False

if boolcheck(os.environ.get("USE_CELERY_EMAIL", True)):
    CELERY_EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"
else:
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

SCOUT_NAME = "MuckRock"

# Sentry
# ------------------------------------------------------------------------------
SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_LOG_LEVEL = int(
    os.environ.get("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)
)  # Alternative to env.int
SENTRY_CELERY_LOGLEVEL = SENTRY_LOG_LEVEL

sentry_logging = LoggingIntegration(
    level=SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR,  # Send errors as events
)
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[sentry_logging, DjangoIntegration(), CeleryIntegration()],
    send_default_pii=True,
)
