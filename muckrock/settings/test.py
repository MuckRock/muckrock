"""
Settings used during testing of the application
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from muckrock.settings.base import *

COMPRESS_ENABLED = False
CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'

PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.MD5PasswordHasher',
            )

INSTALLED_APPS += ('django_nose',)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# minimal middleware for speed
# can I disable more?
MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'lot.middleware.LOTMiddleware',
    'muckrock.middleware.RemoveTokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

BROKER_BACKEND = 'memory'

DEFAULT_FILE_STORAGE = 'inmemorystorage.InMemoryStorage'
