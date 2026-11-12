"""
App config for tasks
"""

# Django
from django.apps import AppConfig


class TaskConfig(AppConfig):
    """App config for tasks"""

    name = "muckrock.task"

    def ready(self):
        """Registers signal handlers"""
        # pylint: disable=unused-import, import-outside-toplevel
        # MuckRock
        import muckrock.task.signals
