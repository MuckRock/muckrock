"""
App config for news
"""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configures the agency application to use activity streams"""
    name = 'muckrock.news'

    def ready(self):
        """Registers articles with the activity streams plugin"""
        from actstream import registry
        registry.register(self.get_model('Article'))
