"""
Settings used when developing locally
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.base import *

DEBUG = True

# Loads static files locally
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATIC_URL = "/static/"
COMPRESS_STORAGE = STATICFILES_STORAGE
COMPRESS_URL = STATIC_URL
COMPRESS_ENABLED = False

MIDDLEWARE += ("muckrock.settings.local.ExceptionLoggingMiddleware",)
MIDDLEWARE = ("silk.middleware.SilkyMiddleware",) + MIDDLEWARE

INSTALLED_APPS += ("silk",)

USE_SILKY = boolcheck(os.environ.get("USE_SILKY", True))
SILKY_PYTHON_PROFILER = USE_SILKY
SILKY_PYTHON_PROFILER_BINARY = USE_SILKY
SILKY_META = USE_SILKY

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "ddt_request_history.panels.request_history.RequestHistoryPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
]


class ExceptionLoggingMiddleware:
    """Log exceptions to command line

    useful for debugging non html outputting views, such as stripe webhooks"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # pylint: disable=unused-argument, import-outside-toplevel
        """printe the exception traceback"""
        import traceback

        print(traceback.format_exc())


DEBUG_TOOLBAR_CONFIG = {
    # always show the toolbar locally
    "SHOW_TOOLBAR_CALLBACK": lambda _: True,
    "JQUERY_URL": "",
}

EMAIL_HOST = "dev.mailhog.com"
EMAIL_PORT = 1025
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

QUERYCOUNT = {"DISPLAY_DUPLICATES": 10}

CACHE_DEBUG = False
if CACHE_DEBUG:
    CACHES["default"] = {
        # Use pylibmc
        "BACKEND": "django_pylibmc.memcached.PyLibMCCache",
        "LOCATION": "127.0.0.1:11211",
        # Use binary memcache protocol (needed for authentication)
        "BINARY": True,
        # TIMEOUT is not the connection timeout! It's the default expiration
        # timeout that should be applied to keys! Setting it to `None`
        # disables expiration.
        "TIMEOUT": None,
        "OPTIONS": {
            # Enable faster IO
            "no_block": True,
            "tcp_nodelay": True,
            # Keep connection alive
            "tcp_keepalive": True,
            # Timeout for set/get requests
            "_poll_timeout": 2000,
            # Use consistent hashing for failover
            "ketama": True,
            # Configure failover timings
            "connect_timeout": 2000,
            "remove_failed": 4,
            "retry_timeout": 2,
            "dead_timeout": 10,
        },
    }

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "[::1]",
    "dev.muckrock.com",
    "dev.foiamachine.org",
]
