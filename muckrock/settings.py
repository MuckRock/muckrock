"""
Django settings for muckrock project
"""

import os
import urlparse


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
USE_TZ = False

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

PREPEND_WWW = os.environ.get('PREPEND_WWW', False)

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
    STATICFILES_STORAGE = 'muckrock.storage.S3StaticStorage'
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

AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)


MIDDLEWARE_CLASSES = (
    'sslify.middleware.SSLifyMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pingback.middleware.PingbackMiddleware',
    'muckrock.middleware.AuthKeyMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
if DEBUG:
    MIDDLEWARE_CLASSES += ('muckrock.settings.ExceptionLoggingMiddleware',)

class ExceptionLoggingMiddleware(object):
    """Log exceptions to command line
    
    useful for debugging non html outputting views, such as stripe webhooks"""
    # pylint: disable=R0903
    # pylint: disable=R0201
    def process_exception(self, request, exception):
        # pylint: disable=W0613
        """printe the exception traceback"""
        import traceback
        print traceback.format_exc()


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
    'django.contrib.flatpages',
    'django.contrib.humanize',
    'django.contrib.markup',
    'django.contrib.staticfiles',
    #'staticfiles',
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
    'django_tablib',
    'urlauth',
    'epiceditor',
    'markdown_deux',
    'muckrock.accounts',
    'muckrock.foia',
    'muckrock.news',
    'muckrock.templatetags',
    'muckrock.tags',
    'muckrock.agency',
    'muckrock.jurisdiction',
    'muckrock.business_days',
    'muckrock.qanda',
    'muckrock.crowdfund',
    'muckrock.sidebar',
)


def show_toolbar(request):
    """show toolbar for me on the site"""
    if DEBUG or (boolcheck(os.environ.get('SHOW_DDT', False)) and
            request.user and request.user.username == 'mitch'):
        return True
    return False

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    'INTERCEPT_REDIRECTS': False,
}

urlparse.uses_netloc.append('redis')
urlparse.uses_netloc.append('amqp')
urlparse.uses_netloc.append('ironmq')
if 'REDISTOGO_URL' in os.environ:
    BROKER_URL = os.environ['REDISTOGO_URL']
elif 'IRON_MQ_PROJECT_ID' in os.environ:
    BROKER_URL = 'ironmq://%s:%s@' % (os.environ.get('IRON_MQ_PROJECT_ID'),
                                      os.environ.get('IRON_MQ_TOKEN'))
else:
    BROKER_URL = 'amqp://muckrock:muckrock@localhost:5672/muckrock_vhost'

import djcelery
# pylint: disable=W0611
import iron_celery
# pylint: enable=W0611
djcelery.setup_loader()

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERY_SEND_EVENT = True
CELERY_IGNORE_RESULTS = True
CELERY_IMPORTS = ('muckrock.foia.tasks', 'muckrock.accounts.tasks')

AUTH_PROFILE_MODULE = 'accounts.Profile'
AUTHENTICATION_BACKENDS = ('muckrock.accounts.backends.CaseInsensitiveModelBackend',)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
SOUTH_TESTS_MIGRATE = False

HAYSTACK_SITECONF = 'muckrock.search_sites'
HAYSTACK_SEARCH_ENGINE = os.environ.get('HAYSTACK_SEARCH_ENGINE', 'whoosh')

TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',
    'theme_advanced_buttons1': 'bold,italic,underline,strikethrough,|,indent,outdent,blockquote,|,'
                               'undo,redo,|,bullist,numlist,|,link,unlink,image,|,cleanup,code',
    'theme_advanced_buttons2': '',
    'theme_advanced_buttons3': '',
    'theme_advanced_statusbar_location': 'none',
    'convert_urls': False,
}

if HAYSTACK_SEARCH_ENGINE == 'whoosh':
    HAYSTACK_WHOOSH_PATH = os.path.join(SITE_ROOT, 'whoosh/mysite_index')
elif HAYSTACK_SEARCH_ENGINE == 'solr':
    HAYSTACK_SOLR_URL = os.environ.get('WEBSOLR_URL', '')

URLAUTH_AUTHKEY_TIMEOUT = 60 * 60 * 24 * 2
URLAUTH_AUTHKEY_NAME = 'authkey'

ASSETS_DEBUG = False

MONTHLY_REQUESTS = {
    'admin': 20,
    'beta': 5,
    'community': 0,
    'pro': 20,
}

MARKDOWN_DEUX_STYLES = {
    "default": {
        "extras": {
            "code-friendly": None,
        },
        "safe_mode": "escape",
    },
    "trusted": {
        "extras": {
            "code-friendly": None,
        },
        "safe_mode": False,
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['console', 'sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'WARNING',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'WARNING',
        },
        'django.request': {
            'handlers': ['sentry'],
            'level': 'ERROR',
            'propagate': False,
        },
        'muckrock': {
            'handlers': ['console', 'mail_admins', 'sentry'],
            'level': 'WARNING',
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

# pylint: disable=W0611
import monkey

# these will be set in local settings if not in env var

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_AUTOIMPORT_BUCKET_NAME = os.environ.get('AWS_AUTOIMPORT_BUCKET_NAME')

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUB_KEY = os.environ.get('STRIPE_PUB_KEY')

MAILGUN_ACCESS_KEY = os.environ.get('MAILGUN_ACCESS_KEY')
MAILGUN_SERVER_NAME = 'requests.muckrock.com'

EMAIL_SUBJECT_PREFIX = '[Muckrock]'
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

if 'MEMCACHIER_SERVERS' in os.environ:
    CACHES['default']['BACKEND'] = 'django.core.cache.backends.memcached.MemcachedCache'
    CACHES['default']['LOCATION'] = '%s:11211' % os.environ.get('MEMCACHIER_SERVERS')
    

# pylint: disable=W0401
# pylint: disable=W0614
try:
    from local_settings import *
except ImportError:
    pass

