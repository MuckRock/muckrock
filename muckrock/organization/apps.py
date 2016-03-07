"""
App config for Organization
"""

from django.apps import AppConfig

import actstream
import watson

class OrganizationConfig(AppConfig):
    """Configures the foia application to use activity streams"""
    name = 'muckrock.organization'

    def ready(self):
        """Registers requests and communications with the activity streams plugin"""
        org = self.get_model('Organization')
        actstream.registry.register(org)
