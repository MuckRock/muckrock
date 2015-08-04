"""
App config for accounts
"""

from django.apps import AppConfig

from actstream import registry

class AccountsConfig(AppConfig):
    """Configures the accounts application to use activity streams"""
    name = 'accounts'

    def ready(self):
        """Registers users with the activity streams plugin"""
        registry.register(self.get_model('User'))
