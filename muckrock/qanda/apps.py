"""
App config for qanda
"""

from django.apps import AppConfig

import actstream
import watson

class QuestionConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'muckrock.qanda'

    def ready(self):
        """Registers the application with plugins"""
        question = self.get_model('Question')
        actstream.registry.register(question)
        watson.register(question)
