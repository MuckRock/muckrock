"""
App config for crowdfunds
"""

# Django
from django.apps import AppConfig


class CrowdfundConfig(AppConfig):
    """Configures the crowdfund application to use activity streams"""
    name = 'muckrock.crowdfund'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        from actstream import registry
        registry.register(self.get_model('Crowdfund'))
        registry.register(self.get_model('CrowdfundPayment'))
