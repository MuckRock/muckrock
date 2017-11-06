"""
App config for news
"""

from django.apps import AppConfig

# pylint: disable=invalid-name

class NewsConfig(AppConfig):
    """Configures the news application to use activity streams"""
    name = 'muckrock.news'

    def ready(self):
        """Registers articles with the activity streams plugin"""
        from actstream import registry as action
        from watson import search
        Article = self.get_model('Article')
        action.register(Article)
        search.register(Article.objects.get_published())
