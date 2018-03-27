"""
Django settings for muckrock project
"""

# Django
from django.core.urlresolvers import reverse

# Standard Library
import os
import urlparse
from collections import OrderedDict
from datetime import date

# Third Party
import djcelery


def boolcheck(setting):
    """Turn env var into proper bool"""
    if isinstance(setting, basestring):
        return setting.lower() in ("yes", "true", "t", "1")
    else:
        return bool(setting)


DEBUG = False
EMAIL_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG
AWS_DEBUG = True

SITE_ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

DEFAULT_FROM_EMAIL = 'MuckRock <info@muckrock.com>'

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

DOGSLOW = True
DOGSLOW_LOG_TO_FILE = False
DOGSLOW_TIMER = 25
DOGSLOW_EMAIL_TO = 'mitch@muckrock.com'
DOGSLOW_EMAIL_FROM = 'info@muckrock.com'
DOGSLOW_LOGGER = 'dogslow'  # can be anything, but must match `logger` below
DOGSLOW_LOG_TO_SENTRY = True

ADMINS = (('Mitchell Kotler', 'mitch@muckrock.com'),)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')
ASSETS_ROOT = os.path.join(SITE_ROOT, 'assets')
COMPRESS_ROOT = ASSETS_ROOT

STATICFILES_DIRS = (os.path.join(SITE_ROOT, 'assets'),)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': os.path.join(SITE_ROOT, 'assets/webpack-stats.json'),
    }
}

COMPRESS_OFFLINE = True

COMPRESS_STORAGE = 'compressor.storage.CompressorFileStorage'
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
# Don't do any JS compression here
# 1. It can cause bugs which means the resulting JS has a syntax error
# 2. We compress the javascript in the webpack config when built for production
COMPRESS_JS_FILTERS = []

THUMBNAIL_CACHE_DIMENSIONS = True

if AWS_DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    THUMBNAIL_DEFAULT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    COMPRESS_STORAGE = STATICFILES_STORAGE
    STATIC_URL = 'https://muckrock-devel2.s3.amazonaws.com/'
    COMPRESS_URL = STATIC_URL
    MEDIA_URL = 'https://muckrock-devel2.s3.amazonaws.com/media/'
    CLEAN_S3_ON_FOIA_DELETE = True
    USE_QUEUED_STORAGE = True
    DIET_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    DIET_CONFIG = os.path.join(SITE_ROOT, '../config/image_diet.yaml')
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    CLEAN_S3_ON_FOIA_DELETE = False
    USE_QUEUED_STORAGE = False

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

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(SITE_ROOT, 'templates'),],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.contrib.auth.context_processors.auth',
            'django.template.context_processors.debug',
            #'django.template.context_processors.i18n',
            'django.template.context_processors.media',
            'django.template.context_processors.request',
            'django.contrib.messages.context_processors.messages',
            'muckrock.sidebar.context_processors.sidebar_info',
            'muckrock.context_processors.google_analytics',
            'muckrock.context_processors.domain',
            'muckrock.context_processors.cache_timeout',
        ],
    }
}]

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django_hosts.middleware.HostsRequestMiddleware',
    'djangosecure.middleware.SecurityMiddleware',
    'dogslow.WatchdogMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'muckrock.middleware.LOTMiddleware',
    'muckrock.middleware.RemoveTokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
)

INTERNAL_IPS = ('127.0.0.1',)

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

ROOT_URLCONF = 'muckrock.urls'

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
    'compressor',
    'corsheaders',
    'debug_toolbar',
    'django_premailer',
    'djangosecure',
    'djcelery',
    'djcelery_email',
    'djgeojson',
    'easy_thumbnails',
    'gunicorn',
    'leaflet',
    'localflavor',
    'mathfilters',
    'news_sitemaps',
    'raven.contrib.django',
    'rest_framework',
    'rest_framework.authtoken',
    'reversion',
    'robots',
    'rules.apps.AutodiscoverRulesConfig',
    'storages',
    'taggit',
    'watson',
    'webpack_loader',
    'lot',
    'image_diet',
    'django_hosts',
    'queued_storage',
    'hijack',
    'compat',  # for hijack
    'django_filters',
    'opensearch',
    'dashing',
    'constance',
    'constance.backends.database',
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
    'muckrock.map',
    'muckrock.message',
    'muckrock.organization',
    'muckrock.project',
    'muckrock.mailgun',
    'muckrock.foiamachine',
    'muckrock.fine_uploader',
    'muckrock.communication',
    'muckrock.portal',
    'muckrock.dataset',
    'muckrock.crowdsource',
    'actstream'
)


def show_toolbar(request):
    """show toolbar on the site"""
    if ((boolcheck(os.environ.get('SHOW_DDT', False)))
        or (request.user and request.user.username == 'mitch')):
        return True
    return False


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
    'INTERCEPT_REDIRECTS': False,
    'JQUERY_URL': '',
}

DEBUG_TOOLBAR_PATCH_SETTINGS = False

urlparse.uses_netloc.append('redis')

BROKER_URL = os.environ.get(
    'REDISTOGO_URL', os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 25 * 60 * 60}

djcelery.setup_loader()

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERY_SEND_EVENT = True
CELERY_IGNORE_RESULTS = True
CELERY_IMPORTS = (
    'muckrock.foia.tasks',
    'muckrock.accounts.tasks',
    'muckrock.agency.tasks',
    'muckrock.task.tasks',
    'muckrock.portal.tasks',
    'muckrock.dataset.tasks',
    'muckrock.crowdsource.tasks',
)
CELERYD_MAX_TASKS_PER_CHILD = os.environ.get('CELERYD_MAX_TASKS_PER_CHILD', 100)
CELERYD_TASK_TIME_LIMIT = os.environ.get('CELERYD_TASK_TIME_LIMIT', 5 * 60)
CELERY_ROUTES = {
    'muckrock.foia.tasks.send_fax': {
        'queue': 'phaxio'
    },
}

AUTHENTICATION_BACKENDS = (
    'rules.permissions.ObjectPermissionBackend',
    'muckrock.accounts.backends.CaseInsensitiveModelBackend',
    'lot.auth_backend.LOTBackend',
)
ABSOLUTE_URL_OVERRIDES = {
    'auth.user':
        lambda u: reverse('acct-profile', kwargs={
            'username': u.username
        }),
}

DBSETTINGS_USE_SITES = False

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
    'agency': 0,
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
            'format':
                '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
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
            'class': 'logging.NullHandler',
        },
        'console': {
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
            'handlers': ['console', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
        'muckrock': {
            'handlers': ['console', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console', 'sentry'],
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
AWS_STORAGE_BUCKET_NAME = os.environ.get(
    'AWS_STORAGE_BUCKET_NAME', 'muckrock-devel2'
)
AWS_AUTOIMPORT_BUCKET_NAME = os.environ.get(
    'AWS_AUTOIMPORT_BUCKET_NAME', 'muckrock-autoimprot-devel'
)

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUB_KEY = os.environ.get('STRIPE_PUB_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

MAILCHIMP_API_KEY = os.environ.get('MAILCHIMP_API_KEY', '')
MAILCHIMP_API_ROOT = 'https://us2.api.mailchimp.com/3.0'
MAILCHIMP_LIST_DEFAULT = '20aa4a931d'

MAILGUN_ACCESS_KEY = os.environ.get('MAILGUN_ACCESS_KEY')
MAILGUN_SERVER_NAME = 'requests.muckrock.com'

EMAIL_SUBJECT_PREFIX = '[Muckrock]'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

DOCUMENTCLOUD_USERNAME = os.environ.get('DOCUMENTCLOUD_USERNAME')
DOCUMENTCLOUD_PASSWORD = os.environ.get('DOCUMENTCLOUD_PASSWORD')

PHAXIO_KEY = os.environ.get('PHAXIO_KEY')
PHAXIO_SECRET = os.environ.get('PHAXIO_SECRET')
PHAXIO_BATCH_DELAY = os.environ.get('PHAXIO_BATCH_DELAY', 300)
PHAXIO_CALLBACK_TOKEN = os.environ.get('PHAXIO_CALLBACK_TOKEN')

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')

PUBLICATION_NAME = 'MuckRock'
PUBLICATION_TIME_ZONE = '-05:00'

# Register database schemes in URLs.
urlparse.uses_netloc.append('postgres')

url = urlparse.urlparse(
    os.environ.get(
        'DATABASE_URL', 'postgres://vagrant@localhost/muckrock_remodel'
    )
)

# Update with environment configuration.
DATABASES = {
    'default': {
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port,
        'CONN_MAX_AGE': int(os.environ.get('CONN_MAX_AGE', 500)),
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
DEFAULT_CACHE_TIMEOUT = 15 * 60

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS':
        'muckrock.pagination.StandardPagination',
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    ),
}

if 'ALLOWED_HOSTS' in os.environ:
    ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')
else:
    ALLOWED_HOSTS = []

ACTSTREAM_SETTINGS = {'MANAGER': 'muckrock.managers.MRActionManager'}

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
ROBOTS_SITE_BY_REQUEST = True

PACKAGE_MONITOR_REQUIREMENTS_FILE = os.path.join(
    SITE_ROOT, '../requirements.txt'
)

TAGGIT_CASE_INSENSITIVE = True
TAGGIT_TAGS_FROM_STRING = 'muckrock.tags.models.parse_tags'

ROOT_HOSTCONF = 'muckrock.hosts'
DEFAULT_HOST = 'default'

# Organization Settings

ORG_MIN_SEATS = 3
ORG_PRICE_PER_SEAT = 2000
ORG_REQUESTS_PER_SEAT = 10

# Leaflet Settings
LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (37.8, -96.9),
    'DEFAULT_ZOOM': 4,
    'MIN_ZOOM': 4,
    'MAX_ZOOM': 18,
    'PLUGINS': {
        'search': {
            'css': ['vendor/leaflet-geocoder-control/Control.Geocoder.css',],
            'js': [
                'vendor/leaflet-geocoder-control/Control.Geocoder.js',
                'js/leaflet-form.js'
            ],
            'auto-include':
                True,
        },
        'draw': {
            'css': [
                'leaflet/draw/leaflet.draw.css',
                'leaflet/draw/leaflet.draw.ie.css'
            ],
            'js': ['leaflet/draw/leaflet.draw.js']
        }
    }
}

# development urls
MUCKROCK_URL = 'localhost:8000'
FOIAMACHINE_URL = 'dev.foiamachine.org:8000'

# Limit CORS support to just API endpoints
CORS_URLS_REGEX = r'^/api(_v\d)?/.*$'
# Limit CORS origin to just FOIA machine
CORS_ORIGIN_REGEX_WHITELIST = (
    r'^(https?://)?(\w+\.)?foiamachine\.org(:\d+)?$',
)
CORS_ALLOW_CREDENTIALS = True

# Django Filter settings
FILTERS_HELP_TEXT_EXCLUDE = False
FILTERS_HELP_TEXT_FILTER = False

# fine uploader
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENT_NUM = 3
ALLOWED_FILE_MIMES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/tiff',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.oasis.opendocument.text',
    'text/html',
    'text/plain',
]
ALLOWED_FILE_EXTS = [
    'pdf',
    'jpg',
    'png',
    'tif',
    'doc',
    'docx',
    'odt',
    'html',
    'txt',
]

# for django-phonenumber-field
PHONENUMBER_DB_FORMAT = 'INTERNATIONAL'
PHONENUMBER_DEFAULT_REGION = 'US'
PHONENUMBER_DEFAULT_FORMAT = 'NATIONAL'

OPENSEARCH_CONTACT_EMAIL = 'mitch@muckrock.com'
OPENSEARCH_SHORT_NAME = 'MuckRock'
OPENSEARCH_DESCRIPTION = 'Search MuckRock for public documents and news'

# for generating pdfs using FPDF
FONT_PATH = '/usr/share/fonts/truetype/dejavu/'

CHECK_EMAIL = os.environ.get('CHECK_EMAIL', '')

DASHING = {
    'INSTALLED_WIDGETS': ('number', 'list', 'graph', 'requestlist'),
    'PERMISSION_CLASSES': ('dashing.permissions.IsAdminUser',)
}

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = OrderedDict([
    ('ENABLE_FOLLOWUP', (True, 'Enable automated followups')),
    (
        'ENABLE_WEEKEND_FOLLOWUP',
        (False, 'Enable automated followups during weekends')
    ),
    (
        'ENABLE_ML',
        (True, 'Automatically resolve response tasks by machine learning')
    ),
    (
        'CONFIDENCE_MIN',
        (70, 'Minimum percent confidence level to automatically resolve')
    ),
    (
        'NEW_USER_GOAL_INIT',
        (0, 'Initial goal for monthly new user registration')
    ),
    (
        'NEW_USER_GOAL_GROWTH',
        (1.07, 'Expected monthly growth rate for new user registration')
    ),
    (
        'NEW_USER_START_DATE', (
            date(2018, 1, 1),
            'Month that the initial new user registration goal applies to'
        )
    ),
    ('PAGE_VIEWS_GOAL_INIT', (0, 'Initial goal for monthly page views')),
    (
        'PAGE_VIEWS_GOAL_GROWTH',
        (1.07, 'Expected monthly growth rate for page views')
    ),
    (
        'PAGE_VIEWS_START_DATE',
        (date(2018, 1, 1), 'Month that the initial page views goal applies to')
    ),
])
CONSTANCE_CONFIG_FIELDSETS = {
    'FOIA Options': ('ENABLE_FOLLOWUP', 'ENABLE_WEEKEND_FOLLOWUP'),
    'Machine Learning Options': ('ENABLE_ML', 'CONFIDENCE_MIN'),
    'Dashboard Options': (
        'NEW_USER_GOAL_INIT',
        'NEW_USER_GOAL_GROWTH',
        'NEW_USER_START_DATE',
        'PAGE_VIEWS_GOAL_INIT',
        'PAGE_VIEWS_GOAL_GROWTH',
        'PAGE_VIEWS_START_DATE',
    )
}

# for google analytics
VIEW_ID = os.environ.get('VIEW_ID', '')

HIJACK_AUTHORIZE_STAFF = True

MULTI_REVIEW_AMOUNT = 2
