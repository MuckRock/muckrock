"""
App config for projects
"""

from django.apps import AppConfig

import actstream
import watson

class ProjectConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'muckrock.project'

    def ready(self):
        """Registers the application with the activity streams plugin"""
        project = self.get_model('Project')
        actstream.registry.register(project)
        watson.register(project)
