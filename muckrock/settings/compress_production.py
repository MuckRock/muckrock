"""
Settings for compressing production assets
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.base import *

STORAGES["staticfiles"][
    "BACKEND"
] = "django.contrib.staticfiles.storage.StaticFilesStorage"
COMPRESS_STORAGE = "compressor.storage.CompressorFileStorage"
STORAGES["compressor"]["BACKEND"] = COMPRESS_STORAGE
STATIC_URL = "https://cdn.muckrock.com/"
COMPRESS_URL = STATIC_URL
COMPRESS_ENABLED = True
