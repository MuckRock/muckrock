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
    servers = os.environ.get("MEMCACHIER_SERVERS", "").replace(",", ";")
    os.environ["MEMCACHE_SERVERS"] = servers
    username = os.environ.get("MEMCACHIER_USERNAME", "")
    os.environ["MEMCACHE_USERNAME"] = username
    password = os.environ.get("MEMCACHIER_PASSWORD", "")
    os.environ["MEMCACHE_PASSWORD"] = password

    CACHES["default"] = {
        # Use pylibmc
        "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
        # TIMEOUT is not the connection timeout! It's the default expiration
        # timeout that should be applied to keys! Setting it to `None`
        # disables expiration.
        "TIMEOUT": None,
        "LOCATION": servers,
        "BINARY": True,
        "OPTIONS": {
            # Use binary memcache protocol (needed for authentication)
            "binary": True,
            "username": username,
            "password": password,
            "behaviors": {
                # Enable faster IO
                "no_block": True,
                "tcp_nodelay": True,
                # Keep connection alive
                "tcp_keepalive": True,
                # Timeout settings
                "connect_timeout": 2000,  # ms
                "send_timeout": 750 * 1000,  # us
                "receive_timeout": 750 * 1000,  # us
                "_poll_timeout": 2000,  # ms
                # Better failover
                "ketama": True,
                "remove_failed": 1,
                "retry_timeout": 2,
                "dead_timeout": 30,
            },
        },
    }

CONSTANCE_DATABASE_CACHE_BACKEND = "default"
