"""
Settings used when deployed to the staging server
Imports from the heroku settings
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from muckrock.settings.heroku import *

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

MUCKROCK_URL = 'muckrock-staging.herokuapp.com'
FOIAMACHINE_URL = 'staging.foiamachine.org'
