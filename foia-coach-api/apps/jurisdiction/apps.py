"""
Jurisdiction app configuration.
"""
from django.apps import AppConfig


class JurisdictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.jurisdiction'
    verbose_name = 'Jurisdiction Resources'

    def ready(self):
        # Import signals when app is ready
        # import apps.jurisdiction.signals  # noqa
        pass
