"""
Django settings for muckrock project
"""

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG
EMAIL_DEBUG = DEBUG

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))

ADMINS = (
    ('Mitchell Kotler', 'mitch@muckrock.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'muckrock'             # Or path to database file if using sqlite3.
DATABASE_USER = 'muckrock'             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.csrf.CsrfResponseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'trackback.middleware.PingbackUrlInjectionMiddleware',
)

if DEBUG:
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

INTERNAL_IPS = ('127.0.0.1',)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

ROOT_URLCONF = 'muckrock.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'south',
    'django_nose',
    'debug_toolbar',
    'haystack',
    'django_assets',
    'djcelery',
    'easy_thumbnails',
    'trackback',
    'muckrock.accounts',
    'muckrock.foia',
    'muckrock.news',
    'muckrock.templatetags',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

import djcelery
djcelery.setup_loader()
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "muckrock"
BROKER_PASSWORD = "muckrock"
BROKER_VHOST = "muckrock_vhost"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("foia.tasks", )
CELERY_DISABLE_RATE_LIMITS = True

if EMAIL_DEBUG:
    EMAIL_PORT = 1025
else:
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 25
    EMAIL_HOST_USER = 'notice@muckrock.com'
    EMAIL_HOST_PASSWORD = ''
    EMAIL_SUBJECT_PREFIX = '[Muckrock] '
    EMAIL_USE_TLS = True

AUTH_PROFILE_MODULE = 'accounts.Profile'
AUTHENTICATION_BACKENDS = ('muckrock.accounts.backends.CaseInsensitiveModelBackend',)

TEST_RUNNER = 'django_nose.run_tests'

HAYSTACK_SITECONF = 'muckrock.search_sites'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = os.path.join(SITE_ROOT, 'whoosh/mysite_index')

ASSETS_DEBUG = False
ASSETS_EXPIRE = 'querystring'

MONTHLY_REQUESTS = 5

# pylint: disable-msg=W0401
# pylint: disable-msg=W0614
from local_settings import *
