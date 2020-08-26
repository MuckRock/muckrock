"""
Settings used during testing of the application on codeship
Import from test settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.test import *

MIDDLEWARE += ("debug_toolbar.middleware.DebugToolbarMiddleware",)

DATABASES["default"] = {
    "NAME": "test",
    "USER": os.environ.get("PG_USER"),
    "PASSWORD": os.environ.get("PG_PASSWORD"),
    "HOST": "127.0.0.1",
    "PORT": "5433",  # Port 5435 is Potsgres V11 on codeship
    "ENGINE": "django.db.backends.postgresql_psycopg2",
}
