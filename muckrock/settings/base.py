"""
Django settings for muckrock project
"""

# Django
from celery.concurrency import asynpool
from django.urls import reverse

# Standard Library
import os
import urllib.parse
from collections import OrderedDict
from datetime import date


def boolcheck(setting):
    """Turn env var into proper bool"""
    if isinstance(setting, str):
        return setting.lower() in ("yes", "true", "t", "1")
    else:
        return bool(setting)


# monkey patch celery to prevent Timed out waiting for UP message errors
asynpool.PROC_ALIVE_TIMEOUT = 60.0

DEBUG = False

SITE_ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))

SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

DEFAULT_FROM_EMAIL = os.environ.get("FROM_EMAIL", "info@muckrock.com")
DIAGNOSTIC_EMAIL = os.environ.get("DIAGNOSTIC_EMAIL", "diagnostics@muckrock.com")
SCANS_EMAIL = os.environ.get("SCANS_EMAIL", "scans@muckrock.com")
SCANS_SLACK_EMAIL = os.environ.get("SCANS_SLACK_EMAIL", SCANS_EMAIL)
ASSIGNMENTS_EMAIL = os.environ.get("ASSIGNMENTS_EMAIL", "assignments@muckrock.com")

ADDRESS_NAME = os.environ.get("ADDRESS_NAME", "MuckRock News")
ADDRESS_DEPT = os.environ.get("ADDRESS_DEPT", "DEPT MR {pk}")
ADDRESS_STREET = os.environ.get("ADDRESS_STREET", "411A Highland Ave")
ADDRESS_CITY = os.environ.get("ADDRESS_CITY", "Somerville")
ADDRESS_STATE = os.environ.get("ADDRESS_STATE", "MA")
ADDRESS_ZIP = os.environ.get("ADDRESS_ZIP", "02144-2516")

PHONE_NUMBER = os.environ.get("PHONE_NUMBER", "(617) 299-1832")
PHONE_NUMBER_LINK = os.environ.get(
    "PHONE_NUMBER_LINK", "+1" + PHONE_NUMBER.translate({ord(i): None for i in "()- "})
)


DATA_UPLOAD_MAX_NUMBER_FIELDS = None

DOGSLOW = True
DOGSLOW_LOG_TO_FILE = False
DOGSLOW_TIMER = 25
DOGSLOW_EMAIL_TO = "mitch@muckrock.com"
DOGSLOW_EMAIL_FROM = "info@muckrock.com"
DOGSLOW_LOGGER = "dogslow"  # can be anything, but must match `logger` below
DOGSLOW_LOG_TO_SENTRY = True

ADMINS = (("Mitchell Kotler", "mitch@muckrock.com"),)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "America/New_York"
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
STATIC_ROOT = os.path.join(SITE_ROOT, "static")
MEDIA_ROOT = os.path.join(STATIC_ROOT, "media")
ASSETS_ROOT = os.path.join(SITE_ROOT, "assets")
COMPRESS_ROOT = ASSETS_ROOT

STATICFILES_DIRS = (os.path.join(SITE_ROOT, "assets"),)

WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "bundles/",
        "STATS_FILE": os.path.join(SITE_ROOT, "assets/webpack-stats.json"),
    }
}

COMPRESS_OFFLINE = True

COMPRESS_STORAGE = "compressor.storage.CompressorFileStorage"
COMPRESS_CSS_FILTERS = [
    "compressor.filters.css_default.CssAbsoluteFilter",
    "compressor.filters.cssmin.CSSMinFilter",
]
# Don't do any JS compression here
# 1. It can cause bugs which means the resulting JS has a syntax error
# 2. We compress the javascript in the webpack config when built for production
COMPRESS_JS_FILTERS = []

THUMBNAIL_CACHE_DIMENSIONS = True

# Boto3S3Storage configuration
DEFAULT_FILE_STORAGE = "muckrock.core.storage.MediaRootS3BotoStorage"
THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE
STATICFILES_STORAGE = "muckrock.core.storage.CachedS3Boto3Storage"
COMPRESS_STORAGE = STATICFILES_STORAGE
CLEAN_S3_ON_FOIA_DELETE = True

# Settings for static bucket storage
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "muckrock-devel2")
AWS_AUTOIMPORT_BUCKET_NAME = os.environ.get(
    "AWS_AUTOIMPORT_BUCKET_NAME", "muckrock-autoimprot-devel"
)
AWS_AUTOIMPORT_PATH = os.environ.get("AWS_AUTOIMPORT_PATH", "scans/")
AWS_S3_CUSTOM_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN")
STATIC_URL = (
    f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    if AWS_S3_CUSTOM_DOMAIN
    else f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
)
COMPRESS_URL = STATIC_URL
COMPRESS_ENABLED = True
AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = True
AWS_HEADERS = {
    "Expires": "Thu, 31 Dec 2099 20:00:00 GMT",
    "Cache-Control": "max-age=94608000",
}
AWS_DEFAULT_ACL = os.environ.get("AWS_STORAGE_DEFAULT_ACL", "public-read")
AWS_S3_MAX_MEMORY_SIZE = int(os.environ.get("AWS_S3_MAX_MEMORY_SIZE", 16 * 1024 * 1024))
AWS_S3_MIN_PART_SIZE = int(os.environ.get("AWS_S3_MIN_PART_SIZE", 16 * 1024 * 1024))

# Set these ENV vars for a separate user-data storage bucket
# (otherwise matches storage settings above)
AWS_MEDIA_BUCKET_NAME = os.environ.get("AWS_MEDIA_BUCKET_NAME", AWS_STORAGE_BUCKET_NAME)
AWS_MEDIA_QUERYSTRING_AUTH = os.environ.get(
    "AWS_MEDIA_QUERYSTRING_AUTH", AWS_QUERYSTRING_AUTH
)
AWS_MEDIA_CUSTOM_DOMAIN = os.environ.get("MEDIA_CLOUDFRONT_DOMAIN")
AWS_MEDIA_EXPIRATION_SECONDS = os.environ.get(
    "AWS_MEDIA_EXPIRATION_SECONDS", 432000
)  # Default is 5 days

if AWS_MEDIA_BUCKET_NAME == AWS_STORAGE_BUCKET_NAME:
    # Inherit bucket/cloudfront settings from static data if they match
    MEDIA_URL = ""
    AWS_MEDIA_CUSTOM_DOMAIN = AWS_S3_CUSTOM_DOMAIN
else:
    # Infer the media url from the custom domain or bucket name settings
    MEDIA_URL = (
        f"https://{AWS_MEDIA_CUSTOM_DOMAIN}/"
        if AWS_MEDIA_CUSTOM_DOMAIN
        else f"https://{AWS_MEDIA_BUCKET_NAME}.s3.amazonaws.com/"
    )

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(SITE_ROOT, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                # 'django.template.context_processors.i18n',
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "muckrock.sidebar.context_processors.sidebar_info",
                "muckrock.core.context_processors.google_analytics",
                "muckrock.core.context_processors.mixpanel",
                "muckrock.core.context_processors.domain",
                "muckrock.core.context_processors.settings",
                "muckrock.core.context_processors.cache_timeout",
            ],
            "libraries": {"thumbnail": "easy_thumbnails.templatetags.thumbnail"},
            "debug": True,
        },
    }
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

MIDDLEWARE = (
    "corsheaders.middleware.CorsMiddleware",
    "django_hosts.middleware.HostsRequestMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "dogslow.WatchdogMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "reversion.middleware.RevisionMiddleware",
    "django_hosts.middleware.HostsResponseMiddleware",
)

INTERNAL_IPS = ("127.0.0.1",)

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

ROOT_URLCONF = "muckrock.core.urls"

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.sitemaps",
    "django.contrib.messages",
    "django.contrib.flatpages",
    "django.contrib.humanize",
    "django.contrib.staticfiles",
    "django.forms",
    "compressor",
    "corsheaders",
    "debug_toolbar",
    "django_premailer",
    "djcelery_email",
    "easy_thumbnails",
    "sorl.thumbnail",
    "gunicorn",
    "localflavor",
    "mathfilters",
    "news_sitemaps",
    "raven.contrib.django",
    "rest_framework",
    "rest_framework.authtoken",
    "reversion",
    "robots",
    "rules.apps.AutodiscoverRulesConfig",
    "storages",
    "taggit",
    "watson",
    "webpack_loader",
    "django_hosts",
    "hijack",
    "compat",  # for hijack
    "django_filters",
    "opensearch",
    "constance",
    "constance.backends.database",
    "django_extensions",
    "social_django",
    "muckrock.accounts",
    "muckrock.foia",
    "muckrock.news",
    "muckrock.core",
    "muckrock.tags",
    "muckrock.agency",
    "muckrock.jurisdiction",
    "muckrock.business_days",
    "muckrock.qanda",
    "muckrock.crowdfund",
    "muckrock.sidebar",
    "muckrock.task",
    "muckrock.message",
    "muckrock.organization",
    "muckrock.project",
    "muckrock.mailgun",
    "muckrock.foiamachine",
    "muckrock.fine_uploader",
    "muckrock.communication",
    "muckrock.portal",
    "muckrock.crowdsource",
    "actstream",
)


def show_toolbar(request):
    """show toolbar on the site"""
    if (boolcheck(os.environ.get("SHOW_DDT", False))) or (
        request.user and request.user.username == "mitch"
    ):
        return True
    return False


DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": show_toolbar, "JQUERY_URL": ""}

DEBUG_TOOLBAR_PATCH_SETTINGS = False

urllib.parse.uses_netloc.append("redis")

REDIS_URL = os.environ.get(
    "REDISTOGO_URL", os.environ.get("REDIS_URL", "redis://localhost:6379/0")
)
CELERY_BROKER_URL = REDIS_URL
CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 25 * 60 * 60}

# CELERY_BEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERY_SEND_EVENT = True
CELERY_TASK_IGNORE_RESULTS = True
CELERY_IMPORTS = (
    "muckrock.accounts.tasks",
    "muckrock.agency.tasks",
    "muckrock.crowdsource.tasks",
    "muckrock.foia.tasks",
    "muckrock.portal.tasks",
    "muckrock.squarelet.tasks",
    "muckrock.task.tasks",
)
CELERY_WORKER_MAX_TASKS_PER_CHILD = os.environ.get(
    "CELERY_WORKER_MAX_TASKS_PER_CHILD", 100
)
CELERY_TASK_TIME_LIMIT = os.environ.get("CELERY_TASK_TIME_LIMIT", 5 * 60)
CELERY_TASK_ROUTES = {"muckrock.foia.tasks.send_fax": {"queue": "phaxio"}}
CELERY_WORKER_CONCURRENCY = os.environ.get("CELERY_WORKER_CONCURRENCY")
CELERY_REDIS_MAX_CONNECTIONS = os.environ.get("CELERY_REDIS_MAX_CONNECTIONS")
if CELERY_REDIS_MAX_CONNECTIONS is not None:
    CELERY_REDIS_MAX_CONNECTIONS = int(CELERY_REDIS_MAX_CONNECTIONS)
CELERY_TIMEZONE = TIME_ZONE

AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "muckrock.accounts.backends.SquareletBackend",
    "django.contrib.auth.backends.ModelBackend",
)
ABSOLUTE_URL_OVERRIDES = {
    "auth.user": lambda u: reverse("acct-profile", kwargs={"username": u.username})
}

DBSETTINGS_USE_SITES = False

SESAME_MAX_AGE = 60 * 60 * 24 * 2

ASSETS_DEBUG = False

MONTHLY_REQUESTS = {
    "admin": 20,
    "basic": 0,
    "beta": 5,
    "pro": 20,
    "proxy": 20,
    "org": 50,
    "robot": 0,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {"level": "WARNING", "handlers": ["console", "sentry"]},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "sentry": {
            "level": "ERROR",
            "class": "raven.contrib.django.handlers.SentryHandler",
            "filters": ["require_debug_false"],
        },
        "dogslow": {
            "level": "WARNING",
            "class": "raven.contrib.django.handlers.SentryHandler",
        },
    },
    "loggers": {
        "django": {"handlers": ["null"], "propagate": True, "level": "INFO"},
        "django.request": {
            "handlers": ["console", "sentry"],
            "level": "WARNING",
            "propagate": False,
        },
        "muckrock": {
            "handlers": ["console", "sentry"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console", "sentry"],
            "propagate": False,
        },
        "raven": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "sentry.errors": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
        "dogslow": {"level": "WARNING", "handlers": ["dogslow"]},
    },
}

# these will be set in local settings if not in env var

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get("SECRET_KEY")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUB_KEY = os.environ.get("STRIPE_PUB_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

MAILCHIMP_API_KEY = os.environ.get("MAILCHIMP_API_KEY", "")
MAILCHIMP_API_ROOT = "https://us2.api.mailchimp.com/3.0"
MAILCHIMP_LIST_DEFAULT = "20aa4a931d"

MAILGUN_ACCESS_KEY = os.environ.get("MAILGUN_ACCESS_KEY")
MAILGUN_SERVER_NAME = os.environ.get("MAILGUN_SERVER_NAME", "requests.muckrock.com")
MAILGUN_API_URL = os.environ.get(
    "MAILGUN_API_URL", f"https://api.mailgun.net/v3/{MAILGUN_SERVER_NAME}"
)


EMAIL_SUBJECT_PREFIX = "[Muckrock]"
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)

DOCUMENTCLOUD_BETA_USERNAME = os.environ.get("DOCUMENTCLOUD_BETA_USERNAME")
DOCUMENTCLOUD_BETA_PASSWORD = os.environ.get("DOCUMENTCLOUD_BETA_PASSWORD")

PHAXIO_KEY = os.environ.get("PHAXIO_KEY")
PHAXIO_SECRET = os.environ.get("PHAXIO_SECRET")
PHAXIO_BATCH_DELAY = os.environ.get("PHAXIO_BATCH_DELAY", 300)
PHAXIO_CALLBACK_TOKEN = os.environ.get("PHAXIO_CALLBACK_TOKEN")

LOB_SECRET_KEY = os.environ.get("LOB_SECRET_KEY")
LOB_WEBHOOK_KEY = os.environ.get("LOB_WEBHOOK_KEY", "secret")
LOB_BANK_ACCOUNT_ID = os.environ.get("LOB_BANK_ACCOUNT_ID")

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

PUBLICATION_NAME = "MuckRock"
PUBLICATION_TIME_ZONE = "-05:00"

url = urllib.parse.urlparse(
    os.environ.get("DATABASE_URL", "postgres://vagrant@localhost/muckrock")
)

# Update with environment configuration.
DATABASES = {
    "default": {
        "NAME": url.path[1:],
        "USER": url.username,
        "PASSWORD": url.password,
        "HOST": url.hostname,
        "PORT": url.port,
        "CONN_MAX_AGE": int(os.environ.get("CONN_MAX_AGE", 500)),
        "ENGINE": "django.db.backends.postgresql_psycopg2",
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "lock": {
        "BACKEND": "redis_lock.django_cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
}
DEFAULT_CACHE_TIMEOUT = 15 * 60

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "muckrock.core.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",
    ),
}
MAX_PAGE_SIZE = int(os.environ.get("MAX_PAGE_SIZE", 100))

if "ALLOWED_HOSTS" in os.environ:
    ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(",")
else:
    ALLOWED_HOSTS = []

ACTSTREAM_SETTINGS = {"MANAGER": "muckrock.core.managers.MRActionManager"}

SOUTH_MIGRATION_MODULES = {
    "taggit": "taggit.south_migrations",
    "easy_thumbnails": "easy_thumbnails.south_migrations",
}

ROBOTS_CACHE_TIMEOUT = 60 * 60 * 24
ROBOTS_SITE_BY_REQUEST = True

PACKAGE_MONITOR_REQUIREMENTS_FILE = os.path.join(SITE_ROOT, "../requirements.txt")

TAGGIT_CASE_INSENSITIVE = True
TAGGIT_TAGS_FROM_STRING = "muckrock.tags.models.parse_tags"

ROOT_HOSTCONF = "muckrock.core.hosts"
DEFAULT_HOST = "default"

# Organization Settings

ORG_MIN_SEATS = 3
ORG_PRICE_PER_SEAT = 2000
ORG_REQUESTS_PER_SEAT = 10

# development urls
MUCKROCK_URL = os.environ.get("MUCKROCK_URL", "http://dev.muckrock.com")
FOIAMACHINE_URL = os.environ.get("FOIAMACHINE_URL", "http://dev.foiamachine.org")
SQUARELET_URL = os.environ.get("SQUARELET_URL", "http://dev.squarelet.com")
DOCCLOUD_URL = os.environ.get("DOCCLOUD_URL", "http://www.dev.documentcloud.org")
DOCCLOUD_EMBED_URL = os.environ.get("DOCCLOUD_EMBED_URL", DOCCLOUD_URL)
DOCCLOUD_API_URL = os.environ.get(
    "DOCCLOUD_API_URL", "http://api.dev.documentcloud.org"
)
DOCCLOUD_ASSET_URL = os.environ.get(
    "DOCCLOUD_ASSET_URL", "http://minio.documentcloud.org:9000/documents/"
)

# Limit CORS support to just API endpoints
CORS_URLS_REGEX = r"^/api(_v\d)?/.*$"
# Limit CORS origin to just FOIA machine
CORS_ORIGIN_REGEX_WHITELIST = (r"^(https?://)?(\w+\.)?foiamachine\.org(:\d+)?$",)
CORS_ALLOW_CREDENTIALS = True

# Django Filter settings
FILTERS_HELP_TEXT_EXCLUDE = False
FILTERS_HELP_TEXT_FILTER = False

# fine uploader
MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024
MAX_ATTACHMENT_NUM = 3
# maximum for outgoing messages, including staff
MAX_ATTACHMENT_TOTAL_SIZE = 20 * 1024 * 1024
DEFAULT_UPLOAD_MIME_UNKNOWN = "application/octet-stream"
ALLOWED_FILE_MIMES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "text/html",
    "text/plain",
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]
ALLOWED_FILE_EXTS = [
    "pdf",
    "jpg",
    "png",
    "tif",
    "doc",
    "docx",
    "odt",
    "html",
    "txt",
    "csv",
    "xls",
    "xlsx",
]

# for django-phonenumber-field
PHONENUMBER_DB_FORMAT = "INTERNATIONAL"
PHONENUMBER_DEFAULT_REGION = "US"
PHONENUMBER_DEFAULT_FORMAT = "NATIONAL"

OPENSEARCH_CONTACT_EMAIL = "mitch@muckrock.com"
OPENSEARCH_SHORT_NAME = "MuckRock"
OPENSEARCH_DESCRIPTION = "Search MuckRock for public documents and news"

# for generating pdfs using FPDF
FONT_PATH = "/usr/share/fonts/truetype/dejavu/"

CHECK_EMAIL = os.environ.get("CHECK_EMAIL", "")
CHECK_LIMIT = int(os.environ.get("CHECK_LIMIT", 200))
CHECK_NOTIFICATIONS = boolcheck(os.environ.get("CHECK_NOTIFICATIONS", False))

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_CONFIG = OrderedDict(
    [
        ("ENABLE_FOLLOWUP", (True, "Enable automated followups")),
        (
            "ENABLE_WEEKEND_FOLLOWUP",
            (False, "Enable automated followups during weekends"),
        ),
        (
            "DISABLED_FOLLOWUP_MESSAGE",
            (
                "Automated followups are currently globally disabled.",
                "Message to show while automated followups are disabled",
            ),
        ),
        (
            "FOLLOWUP_DAYS_PORTAL",
            (90, "Number of days between auto followups for requests using a portal"),
        ),
        (
            "FOLLOWUP_DAYS_FEDERAL",
            (30, "Number of days between auto followups for federal requests"),
        ),
        (
            "FOLLOWUP_DAYS_OTHER",
            (15, "Number of days between auto followups for state and local requests"),
        ),
        (
            "MODERATION_KEYWORDS",
            ("!\n?", "Keywords to trigger manual moderation - one per line"),
        ),
        ("AUTO_LOB", (False, "Automatically send snail mail via Lob")),
        ("AUTO_LOB_PAY", (False, "Automatically send checks via Lob")),
        ("AUTO_LOB_APPEAL", (False, "Automatically send appeal snail mail via Lob")),
        (
            "ENABLE_ML",
            (True, "Automatically resolve response tasks by machine learning"),
        ),
        (
            "CONFIDENCE_MIN",
            (70, "Minimum percent confidence level to automatically resolve"),
        ),
        ("NEW_USER_GOAL_INIT", (0, "Initial goal for monthly new user registration")),
        (
            "NEW_USER_GOAL_GROWTH",
            (1.07, "Expected monthly growth rate for new user registration"),
        ),
        (
            "NEW_USER_START_DATE",
            (
                date(2018, 1, 1),
                "Month that the initial new user registration goal applies to",
            ),
        ),
        ("PAGE_VIEWS_GOAL_INIT", (0, "Initial goal for monthly page views")),
        (
            "PAGE_VIEWS_GOAL_GROWTH",
            (1.07, "Expected monthly growth rate for page views"),
        ),
        (
            "PAGE_VIEWS_START_DATE",
            (date(2018, 1, 1), "Month that the initial page views goal applies to"),
        ),
    ]
)
CONSTANCE_CONFIG_FIELDSETS = {
    "FOIA Options": (
        "ENABLE_FOLLOWUP",
        "ENABLE_WEEKEND_FOLLOWUP",
        "DISABLED_FOLLOWUP_MESSAGE",
        "FOLLOWUP_DAYS_PORTAL",
        "FOLLOWUP_DAYS_FEDERAL",
        "FOLLOWUP_DAYS_OTHER",
        "MODERATION_KEYWORDS",
    ),
    "Lob Options": ("AUTO_LOB", "AUTO_LOB_PAY", "AUTO_LOB_APPEAL"),
    "Machine Learning Options": ("ENABLE_ML", "CONFIDENCE_MIN"),
    "Dashboard Options": (
        "NEW_USER_GOAL_INIT",
        "NEW_USER_GOAL_GROWTH",
        "NEW_USER_START_DATE",
        "PAGE_VIEWS_GOAL_INIT",
        "PAGE_VIEWS_GOAL_GROWTH",
        "PAGE_VIEWS_START_DATE",
    ),
}

# for google analytics
VIEW_ID = os.environ.get("VIEW_ID", "")

HIJACK_AUTHORIZE_STAFF = True
HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF = True

MULTI_REVIEW_AMOUNT = 2

MIXPANEL_TOKEN = os.environ.get("MIXPANEL_TOKEN", "f0342a5341ddad56dfa73505aa604c74")

ZOHO_TOKEN = os.environ.get("ZOHO_TOKEN")
ZOHO_URL = os.environ.get("ZOHO_URL", "https://desk.zoho.com/api/v1/")
ZOHO_ORG_ID = os.environ.get("ZOHO_ORG_ID", "669309916")
ZOHO_DEPT_IDS = {
    "muckrock": os.environ.get("ZOHO_DEPT_ID_MR", "280313000000006907"),
    "documentcloud": os.environ.get("ZOHO_DEPT_ID_DC", "280313000000190114"),
    "foiamachine": os.environ.get("ZOHO_DEPT_ID_FM", "280313000000194669"),
}

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_SQUARELET_KEY = os.environ.get("SQUARELET_KEY")
SOCIAL_AUTH_SQUARELET_SECRET = SQUARELET_SECRET = os.environ.get("SQUARELET_SECRET")
SOCIAL_AUTH_SQUARELET_SCOPE = ["uuid", "organizations", "preferences"]
SOCIAL_AUTH_SQUARELET_AUTH_EXTRA_ARGUMENTS = {"intent": "muckrock"}
SOCIAL_AUTH_TRAILING_SLASH = False

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "muckrock.accounts.pipeline.associate_by_uuid",
    "social_core.pipeline.user.create_user",
    "muckrock.accounts.pipeline.save_profile",
    "muckrock.accounts.pipeline.save_session_data",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)
SOCIAL_AUTH_LOGIN_ERROR_URL = "/"

# this allows communication from muckrock to squarelet to bypass rate limiting
BYPASS_RATE_LIMIT_SECRET = os.environ.get("BYPASS_RATE_LIMIT_SECRET", "")

# for sorl-thumbnails to avoid error
# https://github.com/jazzband/sorl-thumbnail/issues/564
THUMBNAIL_PRESERVE_FORMAT = True
# For easy thumbnails
THUMBNAIL_PRESERVE_EXTENSIONS = ("png",)

# Google Tag Manager
USE_GOOGLE_TAG_MANAGER = boolcheck(os.environ.get("USE_GOOGLE_TAG_MANAGER", False))

# Plaid allows programtic access to our bank account transactions
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
PLAID_SECRET = os.environ.get("PLAID_SECRET")
PLAID_PUBLIC_KEY = os.environ.get("PLAID_PUBLIC_KEY")
PLAID_ENV = os.environ.get("PLAID_ENV", "development")
PLAID_ACCESS_TOKEN = os.environ.get("PLAID_ACCESS_TOKEN")

# ZenDesk
USE_ZENDESK = boolcheck(os.environ.get("USE_ZENDESK", False))
ZENDESK_TOKEN = os.environ.get("ZENDESK_TOKEN", "")
ZENDESK_EMAIL = os.environ.get("ZENDESK_EMAIL", "")
ZENDESK_SUBDOMAIN = os.environ.get("ZENDESK_SUBDOMAIN", "muckrock")

X_FRAME_OPTIONS = "SAMEORIGIN"

USE_SCOUT = False

DOCCLOUD_EXTENSIONS = os.environ.get("DOCCLOUD_EXTENSIONS", ".pdf,.doc,.docx").split(
    ","
)
DOCCLOUD_PROCESSING_WAIT = int(os.environ.get("DOCCLOUD_PROCESSING_WAIT", 60))

AGENCY_SESSION_TIME = int(os.environ.get("AGENCY_SESSION_TIME", 7200))

FOIA_TASKS_STAFF_ONLY = boolcheck(os.environ.get("FOIA_TASKS_STAFF_ONLY", True))
