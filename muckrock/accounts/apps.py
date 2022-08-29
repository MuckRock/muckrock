"""
App config for accounts
"""

# Django
from django.apps import AppConfig, apps


class AccountsConfig(AppConfig):
    """Configures the accounts application to use activity streams"""

    name = "muckrock.accounts"

    def ready(self):
        """Registers users with the activity streams plugin"""
        # pylint: disable=import-outside-toplevel
        # Third Party
        from actstream import registry

        registry.register(apps.get_model("auth.User"))
        registry.register(self.get_model("Profile"))

        # clear all locks in case of crash
        # Django
        from django.core.cache import caches

        caches["lock"].reset_all()
        # require squarelet login for admin
        # Django
        from django.contrib import admin
        from django.contrib.auth.decorators import login_required

        admin.site.login = login_required(admin.site.login)
