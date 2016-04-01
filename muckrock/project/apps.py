"""
App config for projects
"""

from django.apps import AppConfig


class ProjectConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'muckrock.project'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        from actstream import registry
        registry.register(self.get_model('Project'))
