"""
App config for news
"""

from django.apps import AppConfig

from actstream import registry

class NewsConfig(AppConfig):
    """Configures the agency application to use activity streams"""
    name = 'muckrock.news'

    def ready(self):
        """Registers articles with the activity streams plugin"""
        registry.register(self.get_model('Article'))
