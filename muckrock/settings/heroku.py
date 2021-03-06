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

# media and static asset handling
DEFAULT_FILE_STORAGE = "muckrock.core.storage.MediaRootS3BotoStorage"
THUMBNAIL_DEFAULT_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "muckrock.core.storage.CachedS3Boto3Storage"
COMPRESS_STORAGE = STATICFILES_STORAGE
AWS_S3_CUSTOM_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN")
if AWS_S3_CUSTOM_DOMAIN:
    STATIC_URL = "https://" + AWS_S3_CUSTOM_DOMAIN + "/"
else:
    STATIC_URL = "https://" + AWS_STORAGE_BUCKET_NAME + ".s3.amazonaws.com/"
COMPRESS_URL = STATIC_URL
MEDIA_URL = STATIC_URL + "media/"
CLEAN_S3_ON_FOIA_DELETE = True
COMPRESS_ENABLED = True

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
