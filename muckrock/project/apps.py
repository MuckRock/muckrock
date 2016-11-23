"""
App config for projects
"""

from django.apps import AppConfig

# pylint: disable=invalid-name

class ProjectConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'muckrock.project'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        from actstream import registry as action
        from watson import search
        Project = self.get_model('Project')
        action.register(Project)
        search.register(Project.objects.get_public())
