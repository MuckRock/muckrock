"""
App config for qanda
"""

from django.apps import AppConfig


class QuestionConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'muckrock.qanda'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        from actstream import registry
        registry.register(self.get_model('Question'))
