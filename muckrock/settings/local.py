"""
Settings used when developing locally
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.base import *

DEBUG = True

# Vite configuration for local development
DJANGO_VITE = {
    "default": {
        "dev_mode": DEBUG,
        "dev_server_protocol": "http",
        "dev_server_host": "localhost",
        "dev_server_port": 4201,
        "manifest_path": os.path.join(SITE_ROOT, "assets/dist/manifest.json"),
    }
}

# Loads static files locally
STORAGES["staticfiles"][
    "BACKEND"
] = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATIC_URL = "/static/"
COMPRESS_STORAGE = STORAGES["staticfiles"]["BACKEND"]
COMPRESS_URL = STATIC_URL
COMPRESS_ENABLED = False

MIDDLEWARE += ("muckrock.settings.local.ExceptionLoggingMiddleware",)
# MIDDLEWARE = ("silk.middleware.SilkyMiddleware",) + MIDDLEWARE

# INSTALLED_APPS += ("silk",)

USE_SILKY = boolcheck(os.environ.get("USE_SILKY", True))
USE_SILKY = False
SILKY_PYTHON_PROFILER = USE_SILKY
SILKY_PYTHON_PROFILER_BINARY = USE_SILKY
SILKY_META = USE_SILKY

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
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
        # Standard Library
        import traceback

        print(traceback.format_exc())


DEBUG_TOOLBAR_CONFIG = {
    # always show the toolbar locally
    "SHOW_TOOLBAR_CALLBACK": lambda _: True,
    "JQUERY_URL": "",
}

EMAIL_HOST = "internal.dev.mailhog.com"
EMAIL_PORT = 1025
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

QUERYCOUNT = {"DISPLAY_DUPLICATES": 10}


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "[::1]",
    "dev.muckrock.com",
    "dev.foiamachine.org",
]
