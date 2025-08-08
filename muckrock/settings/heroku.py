"""
Settings used when deployed on heroku
Not used directly - imported from production and staging settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.base import *

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
