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

# RAG Provider Configuration for Tests (CRITICAL SAFETY MEASURES)
# ============================================================
# Force use of MockProvider to prevent any real API calls during tests
# This is a critical safety measure to prevent accidental API usage and costs
RAG_PROVIDER = 'mock'

# Disable all real API calls in tests - these should NEVER be True in tests
GEMINI_REAL_API_ENABLED = False
OPENAI_REAL_API_ENABLED = False

# If tests need to test provider-specific logic, they should:
# 1. Use MockProvider with configured behavior (preferred)
# 2. Mock the API client at the library level (e.g., with requests_mock)
# 3. Never make real API calls
# ============================================================

# Disable signal handlers in tests (can be overridden in specific tests)
# Tests should explicitly enable signals when needed
