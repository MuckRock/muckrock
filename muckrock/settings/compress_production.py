"""
Settings for compressing production assets
NOTE: Django Compressor has been removed and replaced with Vite.
This file is kept for reference but is no longer used.
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.base import *

STORAGES["staticfiles"][
    "BACKEND"
] = "django.contrib.staticfiles.storage.StaticFilesStorage"
# Django Compressor settings removed - no longer used
# COMPRESS_STORAGE = STORAGES["compressor"]["BACKEND"]
STATIC_URL = "https://cdn.muckrock.com/"
# COMPRESS_URL = STATIC_URL
# COMPRESS_ENABLED = True
