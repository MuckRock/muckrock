"""
Settings used during testing of the application
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# Standard Library
import warnings

# MuckRock
from muckrock.settings.base import *

COMPRESS_ENABLED = False
CACHES["default"]["BACKEND"] = "django.core.cache.backends.dummy.DummyCache"

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

INSTALLED_APPS += ("django_nose",)

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"

SITE_ID = 1

# minimal middleware for speed
# can I disable more?
MIDDLEWARE = (
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
)

BROKER_BACKEND = "memory"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

DEFAULT_FILE_STORAGE = "inmemorystorage.InMemoryStorage"

LOGGING = {}

TEMPLATES[0]["OPTIONS"]["debug"] = True

warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)

CLEAN_S3_ON_FOIA_DELETE = False
