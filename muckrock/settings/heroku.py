"""
Settings used when deployed on heroku
Not used directly - imported from production and staging settings
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from muckrock.settings.base import *

# media and static asset handling
BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
DIET_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
DIET_CONFIG = os.path.join(SITE_ROOT, '../config/image_diet.yaml')
THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'muckrock.storage.CachedS3BotoStorage'
COMPRESS_STORAGE = STATICFILES_STORAGE
AWS_S3_CUSTOM_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN')
if AWS_S3_CUSTOM_DOMAIN:
    STATIC_URL = 'https://' + AWS_S3_CUSTOM_DOMAIN + '/'
else:
    STATIC_URL = 'https://' + BUCKET_NAME + '.s3.amazonaws.com/'
COMPRESS_URL = STATIC_URL
MEDIA_URL = STATIC_URL + 'media/'
CLEAN_S3_ON_FOIA_DELETE = True
USE_QUEUED_STORAGE = True

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

if 'MEMCACHIER_SERVERS' in os.environ:
    os.environ['MEMCACHE_SERVERS'] = os.environ.get('MEMCACHIER_SERVERS', '').replace(',', ';')
    os.environ['MEMCACHE_USERNAME'] = os.environ.get('MEMCACHIER_USERNAME', '')
    os.environ['MEMCACHE_PASSWORD'] = os.environ.get('MEMCACHIER_PASSWORD', '')

    CACHES = {
        'default': {
            # Use pylibmc
            'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',

            # Use binary memcache protocol (needed for authentication)
            'BINARY': True,

            # TIMEOUT is not the connection timeout! It's the default expiration
            # timeout that should be applied to keys! Setting it to `None`
            # disables expiration.
            'TIMEOUT': None,

            'OPTIONS': {
                # Enable faster IO
                'no_block': True,
                'tcp_nodelay': True,

                # Keep connection alive
                'tcp_keepalive': True,

                # Timeout for set/get requests
                '_poll_timeout': 2000,

                # Use consistent hashing for failover
                'ketama': True,

                # Configure failover timings
                'connect_timeout': 2000,
                'remove_failed': 4,
                'retry_timeout': 2,
                'dead_timeout': 10
            }
        }
    }
