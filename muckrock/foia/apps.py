"""
App config for foia
"""

from django.apps import AppConfig

import actstream
import watson

class FOIAConfig(AppConfig):
    """Configures the foia application to use activity streams"""
    name = 'muckrock.foia'

    def ready(self):
        """Registers requests, communications, and notes with plugins"""
        foia = self.get_model('FOIARequest')
        comm = self.get_model('FOIACommunication')
        note = self.get_model('FOIANote')
        actstream.registry.register(foia)
        actstream.registry.register(comm)
        actstream.registry.register(note)
        watson.register(foia)
