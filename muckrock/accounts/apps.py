"""
App config for accounts
"""

# Django
from django.apps import AppConfig, apps


class AccountsConfig(AppConfig):
    """Configures the accounts application to use activity streams"""
    name = 'muckrock.accounts'

    def ready(self):
        """Registers users with the activity streams plugin"""
        # pylint: disable=too-many-locals
        from actstream import registry
        from dashing.utils import router
        registry.register(apps.get_model('auth.User'))
        registry.register(self.get_model('Profile'))
        from muckrock.accounts.widgets import TopWidget
        router.register(TopWidget, 'top_widget')
