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

if "MEMCACHIER_SERVERS" in os.environ:
    os.environ["MEMCACHE_SERVERS"] = os.environ.get("MEMCACHIER_SERVERS", "").replace(
        ",", ";"
    )
    os.environ["MEMCACHE_USERNAME"] = os.environ.get("MEMCACHIER_USERNAME", "")
    os.environ["MEMCACHE_PASSWORD"] = os.environ.get("MEMCACHIER_PASSWORD", "")

    CACHES["default"] = {
        # Use pylibmc
        "BACKEND": "django_pylibmc.memcached.PyLibMCCache",
        # Use binary memcache protocol (needed for authentication)
        "BINARY": True,
        # TIMEOUT is not the connection timeout! It's the default expiration
        # timeout that should be applied to keys! Setting it to `None`
        # disables expiration.
        "TIMEOUT": None,
        "OPTIONS": {
            # Enable faster IO
            "no_block": True,
            "tcp_nodelay": True,
            # Keep connection alive
            "tcp_keepalive": True,
            # Timeout for set/get requests
            "_poll_timeout": 2000,
            # Use consistent hashing for failover
            "ketama": True,
            # Configure failover timings
            "connect_timeout": 2000,
            "remove_failed": 4,
            "retry_timeout": 2,
            "dead_timeout": 10,
        },
    }

CONSTANCE_DATABASE_CACHE_BACKEND = "default"
