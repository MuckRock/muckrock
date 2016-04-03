"""
Settings used when developing locally
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from muckrock.settings.base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
EMAIL_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG
AWS_DEBUG = False

MIDDLEWARE_CLASSES += (
    'muckrock.settings.local.ExceptionLoggingMiddleware',
    'yet_another_django_profiler.middleware.ProfilerMiddleware',
    #'querycount.middleware.QueryCountMiddleware',
    )

DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        ]

class ExceptionLoggingMiddleware(object):
    """Log exceptions to command line

    useful for debugging non html outputting views, such as stripe webhooks"""
    # pylint: disable=too-few-public-methods
    # pylint: disable=no-self-use
    def process_exception(self, request, exception):
        # pylint: disable=unused-argument
        """printe the exception traceback"""
        import traceback
        print traceback.format_exc()

DEBUG_TOOLBAR_CONFIG = {
    # always show the toolbar locally
    'SHOW_TOOLBAR_CALLBACK': lambda _: False,
    'INTERCEPT_REDIRECTS': False,
    'JQUERY_URL': '',
}

EMAIL_PORT = 1025

QUERYCOUNT = {
        'DISPLAY_DUPLICATES': 10,
        }

