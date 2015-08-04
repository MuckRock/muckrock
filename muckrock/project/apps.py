"""
App config for projects
"""

from django.apps import AppConfig

from actstream import registry

class ProjectConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'project'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        registry.register(self.get_model('Project')
