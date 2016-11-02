"""
App config for foia
"""

from django.apps import AppConfig


class FOIAConfig(AppConfig):
    """Configures the foia application to use activity streams"""
    name = 'muckrock.foia'

    def ready(self):
        """Registers requests and communications with the activity streams plugin"""
        from actstream import registry as action
        from watson import search
        FOIARequest = self.get_model('FOIARequest')
        FOIACommunication = self.get_model('FOIACommunication')
        FOIANote = self.get_model('FOIANote')
        action.register(FOIARequest)
        action.register(FOIACommunication)
        action.register(FOIANote)
        search.register(FOIARequest.objects.get_public())
