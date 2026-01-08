"""
Settings used when deployed on heroku
Not used directly - imported from production and staging settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# Standard Library
import logging
import os

# Third Party
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# MuckRock
from muckrock.settings.base import *

# Vite configuration for production
DJANGO_VITE = {
    "default": {
        "dev_mode": False,
        "manifest_path": os.path.join(SITE_ROOT, "assets/dist/manifest.json"),
    }
}

INSTALLED_APPS = ("scout_apm.django",) + INSTALLED_APPS
USE_SCOUT = True

TEMPLATES[0]["OPTIONS"]["loaders"] = [
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]
del TEMPLATES[0]["APP_DIRS"]

CACHES["default"] = {
    "BACKEND": "django_redis.cache.RedisCache",
    "LOCATION": REDIS_URL,
    "OPTIONS": {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        # Mimicing memcache behavior.
        # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
        "IGNORE_EXCEPTIONS": True,
    },
}
if REDIS_URL.startswith("rediss:"):
    CACHES["default"]["OPTIONS"]["CONNECTION_POOL_KWARGS"] = {"ssl_cert_reqs": None}

CONSTANCE_DATABASE_CACHE_BACKEND = "default"

# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
ANYMAIL = {
    "MAILGUN_API_KEY": MAILGUN_ACCESS_KEY,
    "MAILGUN_SENDER_DOMAIN": os.environ.get(
        "MAILGUN_SENDER_DOMAIN", MAILGUN_SERVER_NAME
    ),
    "SEND_DEFAULTS": {
        "track_clicks": True,
        "track_opens": True,
    },
}

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
