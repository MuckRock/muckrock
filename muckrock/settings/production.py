"""
Settings used when deployed to the production server
Imports from the heroku settings
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from muckrock.settings.heroku import *

# Security
SECURE_HSTS_SECONDS = 31536000 #one year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_FRAME_DENY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

PREPEND_WWW = True

EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
