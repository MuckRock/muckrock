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
