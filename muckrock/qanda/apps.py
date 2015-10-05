"""
App config for qanda
"""

from django.apps import AppConfig

from actstream import registry

class QuestionConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'muckrock.qanda'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        registry.register(self.get_model('Question'))
