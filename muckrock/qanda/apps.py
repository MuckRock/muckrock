"""
App config for qanda
"""

# Django
from django.apps import AppConfig


class QuestionConfig(AppConfig):
    """Configures the project application to use activity streams"""

    name = "muckrock.qanda"

    def ready(self):
        """Registers the application with the activity streams plugin"""
        # pylint: disable=invalid-name, import-outside-toplevel
        # Third Party
        from actstream import registry

        Question = self.get_model("Question")
        Answer = self.get_model("Answer")
        registry.register(Question)
        registry.register(Answer)
