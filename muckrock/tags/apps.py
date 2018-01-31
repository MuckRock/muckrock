"""
App config for tags
"""

# Django
from django.apps import AppConfig


class TagConfig(AppConfig):
    """Configures the project application to use activity streams"""
    name = 'muckrock.tags'

    def ready(self):
        """Registers the application with the watson plugin"""
        # pylint: disable=invalid-name
        from watson import search
        Tag = self.get_model('Tag')
        search.register(Tag)
