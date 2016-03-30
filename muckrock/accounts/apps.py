"""
App config for accounts
"""

from django.apps import AppConfig, apps


class AccountsConfig(AppConfig):
    """Configures the accounts application to use activity streams"""
    name = 'muckrock.accounts'

    def ready(self):
        """Registers users with the activity streams plugin"""
        from actstream import registry
        registry.register(apps.get_model('auth.User'))
        registry.register(self.get_model('Profile'))
