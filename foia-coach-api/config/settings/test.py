"""
Test settings for FOIA Coach API service.
"""
from .base import *  # noqa

# Use in-memory SQLite for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}

# Media files in temp directory
MEDIA_ROOT = '/tmp/foia-coach-api-test-media'

# Disable signal handlers in tests (can be overridden in specific tests)
# Tests should explicitly enable signals when needed
