"""
App config for agency
"""

from django.apps import AppConfig

from actstream import registry

class AgencyConfig(AppConfig):
    """Configures the agency application to use activity streams"""
    name = 'muckrock.agency'

    def ready(self):
        """Registers agencies with the activity streams plugin"""
        registry.register(self.get_model('Agency'))
