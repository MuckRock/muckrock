"""
Washington Post setting overrides for staging
"""

import requests

 # pylint: disable=wildcard-import

from muckrock.settings.staging import *

UNINSTALLED_APPS = ["scout_apm.django"]
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in UNINSTALLED_APPS]
USE_SCOUT = False

CONSTANCE_REDIS_CONNECTION = {
    'host': os.environ.get("REDIS_HOST"),
    'port': 6379,
}

# This gets the IP address of the EC2 instance the task is
# running on and adds it to allowed_hosts so the health
# check will work
try:
    EC2_IP = requests.get('http://169.254.169.254/latest/meta-data/local-ipv4').text
    ALLOWED_HOSTS.append(EC2_IP)
except requests.exceptions.RequestException:
    pass
