"""
Washington Post setting overrides for staging
"""
 # pylint: disable=wildcard-import

from muckrock.settings.staging import *

UNINSTALLED_APPS = ["scout_apm.django"]
INSTALLED_APPS = [app for app in settings.INSTALLED_APPS if app not in UNINSTALLED_APPS]
USE_SCOUT = False
