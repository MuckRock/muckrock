"""
App config for jurisdiction
"""

# Django
from django.apps import AppConfig


class JurisdictionConfig(AppConfig):
    """Configures the jurisdiction application to use watson"""
    name = 'muckrock.jurisdiction'

    def ready(self):
        """Registers exemptions with watson"""
        # pylint: disable=invalid-name
        from watson import search
        Exemption = self.get_model('Exemption')
        search.register(Exemption)
