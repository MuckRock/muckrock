"""
App config for agency
"""

# Django
from django.apps import AppConfig


class AgencyConfig(AppConfig):
    """Configures the agency application to use activity streams"""
    name = 'muckrock.agency'

    def ready(self):
        """Registers agencies with the activity streams plugin"""
        # pylint: disable=invalid-name
        from actstream import registry as action
        from watson import search
        Agency = self.get_model('Agency')
        action.register(Agency)
        search.register(Agency.objects.get_approved())
