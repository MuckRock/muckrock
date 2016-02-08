"""
App config for agency
"""

from django.apps import AppConfig

import actstream
import watson

class AgencyConfig(AppConfig):
    """Configures the agency application to use activity streams"""
    name = 'muckrock.agency'

    def ready(self):
        """Registers agencies with the activity streams plugin"""
        Agency = self.get_model('Agency')
        actstream.registry.register(Agency)
        watson.register(Agency.objects.get_approved())
