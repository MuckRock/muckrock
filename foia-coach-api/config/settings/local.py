"""
Local development settings for FOIA Coach API service.
"""
from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'foia_coach_api']

# CORS Configuration for local development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # SvelteKit dev server
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# Django REST Framework - Add browsable API in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [  # noqa
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
