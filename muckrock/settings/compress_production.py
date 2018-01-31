"""
Settings for compressing production assets
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# MuckRock
from muckrock.settings.base import *

STATIC_URL = 'https://cdn.muckrock.com/'
COMPRESS_ENABLED = True
