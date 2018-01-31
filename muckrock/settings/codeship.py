"""
Settings used during testing of the application on codeship
Import from test settings
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.test import *

MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

DATABASES['default'] = {
    'NAME': 'test',
    'USER': os.environ.get('PG_USER'),
    'PASSWORD': os.environ.get('PG_PASSWORD'),
    'HOST': '127.0.0.1',
    'PORT': '5435',  # Port 5435 is Potsgres V9.5 on codeship
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
}
