"""App configuration for the gethelp app"""

# Django
from django.apps import AppConfig


class GetHelpConfig(AppConfig):
    name = "muckrock.gethelp"
    verbose_name = "Get Help"

    def ready(self):
        # pylint: disable=unused-import, import-outside-toplevel
        # MuckRock
        import muckrock.gethelp.signals
