"""
App config for foia
"""

from django.apps import AppConfig


class FOIAConfig(AppConfig):
    """Configures the foia application to use activity streams"""
    name = 'muckrock.foia'

    def ready(self):
        """Registers requests and communications with the activity streams plugin"""
        from actstream import registry
        registry.register(self.get_model('FOIARequest'))
        registry.register(self.get_model('FOIACommunication'))
        registry.register(self.get_model('FOIANote'))
