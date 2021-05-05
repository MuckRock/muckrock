"""
Washington Post setting overrides for production
"""

import requests

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import

from muckrock.settings.production import *
from muckrock.settings.wapo.base import *

# TODO Remove me once we've verified email sending in production
INSTALLED_APPS += ("bandit",)
EMAIL_BACKEND = "muckrock.settings.staging.HijackMailgunBackend"
BANDIT_EMAIL = os.environ.get("BANDIT_EMAIL", "staging@muckrock.com")
BANDIT_WHITELIST = [
    e.strip() for e in os.environ.get("BANDIT_WHITELIST", "").split(",") if e.strip()
]

SECURE_SSL_REDIRECT = False

AWS_STORAGE_BUCKET_NAME="wp-muckrock-prod"
AWS_MEDIA_BUCKET_NAME="wp-muckrock-uploads-prod"
CLOUDFRONT_DOMAIN="wp-muckrock-prod.news-engineering.aws.wapo.pub"
AWS_STORAGE_DEFAULT_ACL="private"
AWS_MEDIA_QUERYSTRING_AUTH=True

MAILGUN_DOMAIN = "foi-requests.washpost.com"

# This gets the IP address of the EC2 instance the task is
# running on and adds it to allowed_hosts so the health
# check will work
try:
    EC2_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4').text
    ALLOWED_HOSTS.append(EC2_IP)
except requests.exceptions.RequestException:
    pass
