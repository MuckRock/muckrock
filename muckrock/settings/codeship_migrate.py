"""
Settings used during migrating of the database on codeship
This is necessary to not promote certain warnings to errors during migration
causing the migrations to fail
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

# Standard Library
import warnings

# MuckRock
from muckrock.settings.codeship import *

# set this warning back to default from an error
warnings.filterwarnings(
    'default',
    r'DateTimeField .* received a naive datetime',
    RuntimeWarning,
    r'django\.db\.models\.fields',
)
