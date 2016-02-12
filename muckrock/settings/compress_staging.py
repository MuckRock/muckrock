"""
Settings for compressing staging assets
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from muckrock.settings.base import *

BUCKET_NAME = 'muckrock-staging'
STATIC_URL = 'https://' + BUCKET_NAME + '.s3.amazonaws.com/'
COMPRESS_ENABLED = True
