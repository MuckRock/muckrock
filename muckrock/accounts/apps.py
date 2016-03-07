"""
App config for accounts
"""

from django.apps import AppConfig
from django.contrib.auth.models import User

import actstream

class AccountsConfig(AppConfig):
    """Configures the accounts application to use activity streams"""
    name = 'muckrock.accounts'

    def ready(self):
        """Registers users with the activity streams plugin"""
        profile = self.get_model('Profile')
        actstream.registry.register(User)
        actstream.registry.register(profile)
