"""
Django settings for muckrock project
"""

import os
import urlparse
from django.core.urlresolvers import reverse

def boolcheck(setting):
    """Turn env var into proper bool"""
    if isinstance(setting, basestring):
        return setting.lower() in ("yes", "true", "t", "1")
    else:
        return bool(setting)

DEBUG = False
TEMPLATE_DEBUG = DEBUG
EMAIL_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG
AWS_DEBUG = False

SITE_ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

DOGSLOW = True
DOGSLOW_LOG_TO_FILE = False
DOGSLOW_TIMER = 25
DOGSLOW_EMAIL_TO = 'mitch@muckrock.com'
DOGSLOW_EMAIL_FROM = 'info@muckrock.com'
DOGSLOW_LOGGER = 'dogslow' # can be anything, but must match `logger` below
DOGSLOW_LOG_TO_SENTRY = True

ADMINS = (
    ('Mitchell Kotler', 'mitch@muckrock.com'),
    ('Allan Lasser', 'allan@muckrock.com'),
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

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')
ASSETS_ROOT = os.path.join(SITE_ROOT, 'assets')
COMPRESS_ROOT = ASSETS_ROOT

STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'assets'),
)

COMPRESS_OFFLINE = True

COMPRESS_STORAGE = 'compressor.storage.CompressorFileStorage'
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'sass --sourcemap=none {infile} {outfile}'),
)

if AWS_DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    COMPRESS_STORAGE = STATICFILES_STORAGE
    STATIC_URL = 'https://muckrock-devel2.s3.amazonaws.com/'
    COMPRESS_URL = STATIC_URL
    MEDIA_URL = 'https://muckrock-devel2.s3.amazonaws.com/media/'
    CLEAN_S3_ON_FOIA_DELETE = True
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    CLEAN_S3_ON_FOIA_DELETE = False

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = True
AWS_S3_FILE_OVERWRITE = False
AWS_HEADERS = {
 'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
 'Cache-Control': 'max-age=94608000',
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'muckrock.sidebar.context_processors.sidebar_info',
    'muckrock.context_processors.google_analytics',
)

MIDDLEWARE_CLASSES = (
    'djangosecure.middleware.SecurityMiddleware',
    'dogslow.WatchdogMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'lot.middleware.LOTMiddleware',
    'muckrock.middleware.RemoveTokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'reversion.middleware.RevisionMiddleware',
)

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
    'autocomplete_light',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'django.contrib.flatpages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'celery_haystack',
    'compressor',
    'debug_toolbar',
    'django_premailer',
    'djangosecure',
    'djcelery',
    'easy_thumbnails',
    'gunicorn',
    'haystack',
    'dbsettings',
    'localflavor',
    'markdown_deux',
    'mathfilters',
    'news_sitemaps',
    'raven.contrib.django',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'reversion',
    'robots',
    'storages',
    'taggit',
    'lot',
    'package_monitor',
    'image_diet',
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
    'muckrock.task',
    'muckrock.message',
    'muckrock.organization',
    'muckrock.project',
    'muckrock.mailgun',
    'actstream'
)

def show_toolbar(request):
    """show toolbar on the site"""
    if ((boolcheck(os.environ.get('SHOW_DDT', False))) or
            (request.user and request.user.username == 'mitch')):
        return True
    return False

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    'INTERCEPT_REDIRECTS': False,
    'JQUERY_URL': '',
}

DEBUG_TOOLBAR_PATCH_SETTINGS = False

urlparse.uses_netloc.append('redis')

BROKER_URL = os.environ.get('REDISTOGO_URL', 'redis://localhost:6379/0')

import djcelery
djcelery.setup_loader()

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERY_SEND_EVENT = True
CELERY_IGNORE_RESULTS = True
CELERY_IMPORTS = (
    'muckrock.foia.tasks',
    'muckrock.accounts.tasks',
    'muckrock.agency.tasks',
    )
CELERYD_MAX_TASKS_PER_CHILD = os.environ.get('CELERYD_MAX_TASKS_PER_CHILD', 100)
CELERYD_TASK_TIME_LIMIT = os.environ.get('CELERYD_TASK_TIME_LIMIT', 5 * 60)

AUTHENTICATION_BACKENDS = (
    'muckrock.accounts.backends.CaseInsensitiveModelBackend',
    'lot.auth_backend.LOTBackend',
    )
ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: reverse('acct-profile', kwargs={'username': u.username}),
}

DBSETTINGS_USE_SITES = True

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(SITE_ROOT, 'whoosh/mysite_index'),
        'STORAGE': 'file',
        'POST_LIMIT': 128 * 1024 * 1024,
        'INCLUDE_SPELLING': True,
        'BATCH_SIZE': 100,
    },
}

HAYSTACK_SIGNAL_PROCESSOR = 'muckrock.signals.RelatedCelerySignalProcessor'

SESAME_MAX_AGE = 60 * 60 * 24 * 2

ASSETS_DEBUG = False

MONTHLY_REQUESTS = {
    'admin': 20,
    'basic': 0,
    'beta': 5,
    'pro': 20,
    'proxy': 20,
    'org': 50,
    'robot': 0,
}

BUNDLED_REQUESTS = {
    'admin': 5,
    'basic': 4,
    'beta': 4,
    'pro': 5,
    'proxy': 5,
    'org': 5,
    'robot': 0,
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
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['require_debug_false'],
        },
        'dogslow': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.handlers.SentryHandler',
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
        'dogslow': {
            'level': 'WARNING',
            'handlers': ['dogslow'],
        },
    }
}

# these will be set in local settings if not in env var

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'muckrock-devel2')
AWS_AUTOIMPORT_BUCKET_NAME = os.environ.get(
    'AWS_AUTOIMPORT_BUCKET_NAME', 'muckrock-autoimprot-devel')

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUB_KEY = os.environ.get('STRIPE_PUB_KEY')

MAILGUN_ACCESS_KEY = os.environ.get('MAILGUN_ACCESS_KEY')
MAILGUN_SERVER_NAME = 'requests.muckrock.com'

EMAIL_SUBJECT_PREFIX = '[Muckrock]'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

DOCUMENTCLOUD_USERNAME = os.environ.get('DOCUMENTCLOUD_USERNAME')
DOCUMENTCLOUD_PASSWORD = os.environ.get('DOCUMENTCLOUD_PASSWORD')

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')

PUBLICATION_NAME = 'MuckRock'

# Register database schemes in URLs.
urlparse.uses_netloc.append('postgres')

url = urlparse.urlparse(os.environ.get('DATABASE_URL', 'postgres://muckrock@localhost/muckrock'))

# Update with environment configuration.
DATABASES = {
        'default': {
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
            'CONN_MAX_AGE': os.environ.get('CONN_MAX_AGE', 500),
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            }
        }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

REST_FRAMEWORK = {
    'PAGINATE_BY': 20,                 # Default to 20
    'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
    'MAX_PAGINATE_BY': 100,            # Maximum limit allowed when using `?page_size=xxx`.
    'DEFAULT_FILTER_BACKENDS':
        ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES':
        ('rest_framework.authentication.TokenAuthentication',
         'rest_framework.authentication.SessionAuthentication',),
    'DEFAULT_PERMISSION_CLASSES':
        ('rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',),
}

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

ACTSTREAM_SETTINGS = {
    'MANAGER': 'muckrock.managers.MRActionManager'
}

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
    'easy_thumbnails': 'easy_thumbnails.south_migrations',
}

LOT = {
  'slow-login': {
      'name': u'Slow login',
      'duration': 60 * 60 * 24 * 2,
      'one-time': True,
  },
}
LOT_MIDDLEWARE_PARAM_NAME = 'uuid-login'

ROBOTS_CACHE_TIMEOUT = 60 * 60 * 24

PACKAGE_MONITOR_REQUIREMENTS_FILE = os.path.join(SITE_ROOT, '../requirements.txt')

# Organization Settings

ORG_MIN_SEATS = 3
ORG_PRICE_PER_SEAT = 2000
ORG_REQUESTS_PER_SEAT = 10

