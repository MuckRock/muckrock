"""
App config for news
"""

from django.apps import AppConfig

import actstream
import watson

class NewsConfig(AppConfig):
    """Configures the agency application to use activity streams"""
    name = 'muckrock.news'

    def ready(self):
        """Registers articles with plugins"""
        Article = self.get_model('Article')
        actstream.registry.register(Article)
        watson.register(Article.objects.get_published())
