"""
App config for accounts
"""

from django.apps import AppConfig
from django.contrib.auth.models import User

from actstream import registry

class AccountsConfig(AppConfig):
    """Configures the accounts application to use activity streams"""
    name = 'muckrock.accounts'

    def ready(self):
        """Registers users with the activity streams plugin"""
        registry.register(User)
        registry.register(self.get_model('Profile'))
