"""
App config for crowdfunds
"""

from django.apps import AppConfig

from actstream import registry

class CrowdfundConfig(AppConfig):
    """Configures the crowdfund application to use activity streams"""
    name = 'muckrock.crowdfund'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        registry.register(self.get_model('Crowdfund'))
        registry.register(self.get_model('CrowdfundPayment'))
