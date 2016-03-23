"""
App config for Organization
"""

from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    """Configures the foia application to use activity streams"""
    name = 'muckrock.organization'

    def ready(self):
        """Registers requests and communications with the activity streams plugin"""
        from actstream import registry
        registry.register(self.get_model('Organization'))
