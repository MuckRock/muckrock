"""
Django settings for muckrock project
"""

import os
import urlparse

import logging

def boolcheck(setting):
    """Turn env var into proper bool"""
    if isinstance(setting, basestring):
        return setting.lower() in ("yes", "true", "t", "1")
    else:
        return bool(setting)

DEBUG = boolcheck(os.environ.get('DEBUG', True))
TEMPLATE_DEBUG = DEBUG
EMAIL_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))

ADMINS = (
    ('Mitchell Kotler', 'mitch@muckrock.com'),
)

MANAGERS = ADMINS

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
STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')
ASSETS_ROOT = os.path.join(SITE_ROOT, 'assets')


STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'assets'),
)

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    STATIC_URL = 'https://muckrock.s3.amazonaws.com/'
    MEDIA_URL = 'https://muckrock.s3.amazonaws.com/media/'
else:
    #DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    #THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    #STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    #STATIC_URL = 'https://muckrock-devel2.s3.amazonaws.com/'
    #MEDIA_URL = 'https://muckrock-devel2.s3.amazonaws.com/media/'
    STATICFILES_STORAGE = 'staticfiles.storage.StaticFilesStorage'
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'


AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = False


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
    'pingback.middleware.PingbackMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)
if DEBUG:
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)


INTERNAL_IPS = ('127.0.0.1',)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

ROOT_URLCONF = 'urls'

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
    'django.contrib.flatpages',
    'django.contrib.humanize',
    'raven.contrib.django',
    'gunicorn',
    'south',
    'django_nose',
    'debug_toolbar',
    'haystack',
    'django_assets',
    'djcelery',
    'easy_thumbnails',
    'pingback',
    'taggit',
    'dbsettings',
    'storages',
    'staticfiles',
    'accounts',
    'foia',
    'rodeo',
    'news',
    'templatetags',
    'tags',
    'agency',
    'jurisdiction',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

urlparse.uses_netloc.append('redis')
urlparse.uses_netloc.append('amqp')
#url = urlparse.urlparse(os.environ.get('REDISTOGO_URL', 'redis://localhost:6379/'))
url = urlparse.urlparse(os.environ.get('CLOUDAMQP_URL',
    'amqp://muckrock:muckrock@localhost:5672/muckrock_vhost'))

import djcelery
djcelery.setup_loader()

BROKER_HOST = url.hostname
BROKER_PORT = url.port
BROKER_USER = url.username
BROKER_PASSWORD = url.password
# pylint: disable=E1101
BROKER_VHOST = url.path[1:]
# pylint: enable=E1101

# for redis only:
#BROKER_VHOST = '0'
#REDIS_PORT = BROKER_PORT
#REDIS_HOST = BROKER_HOST
#REDIS_DB = 0
#REDIS_CONNECT_RETRY = True
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERY_SEND_EVENT = True
CELERY_IGNORE_RESULTS = True
CELERY_IMPORTS = ('muckrock.foia.tasks', 'muckrock.accounts.tasks')

AUTH_PROFILE_MODULE = 'accounts.Profile'
AUTHENTICATION_BACKENDS = ('accounts.backends.CaseInsensitiveModelBackend',)

TEST_RUNNER = 'django_nose.run_tests'

HAYSTACK_SITECONF = 'search_sites'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = os.path.join(SITE_ROOT, 'whoosh/mysite_index')

ASSETS_DEBUG = False

MONTHLY_REQUESTS = {
    'admin': 100,
    'beta': 5,
    'community': 0,
    'pro': 20,
}

MAILGUN_SERVER_NAME = 'requests.muckrock.com'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# pylint: disable=W0611
import monkey

# these will be set in local settings if not in env var

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUB_KEY = os.environ.get('STRIPE_PUB_KEY')

MAILGUN_ACCESS_KEY = os.environ.get('MAILGUN_ACCESS_KEY')

DOCUMNETCLOUD_USERNAME = os.environ.get('DOCUMNETCLOUD_USERNAME')
DOCUMENTCLOUD_PASSWORD = os.environ.get('DOCUMENTCLOUD_PASSWORD')

GA_USERNAME = os.environ.get('GA_USERNAME')
GA_PASSWORD = os.environ.get('GA_PASSWORD')
GA_ID = os.environ.get('GA_ID')

# Register database schemes in URLs.
urlparse.uses_netloc.append('postgres')
urlparse.uses_netloc.append('mysql')

DATABASES = {}

url = urlparse.urlparse(os.environ.get('DATABASE_URL', 'postgres://muckrock@localhost/muckrock'))

# pylint: disable=E1101
# Update with environment configuration.
DATABASES['default'] = {
    'NAME': url.path[1:],
    'USER': url.username,
    'PASSWORD': url.password,
    'HOST': url.hostname,
    'PORT': url.port,
}

# test runner seems to want this...
DATABASE_NAME = DATABASES['default']['NAME']

if url.scheme == 'postgres':
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'

if url.scheme == 'mysql':
    DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'

if 'MEMCACHIER_SERVERS' in os.environ:
    CACHE_BACKEND = 'memcached://%s:11211/' % os.environ.get('MEMCACHIER_SERVERS')
else:
    CACHE_BACKEND = 'dummy://'

# pylint: disable=W0401
# pylint: disable=W0614
try:
    from local_settings import *
except ImportError:
    pass

