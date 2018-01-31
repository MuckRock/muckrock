"""
App config for news
"""

# Django
from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configures the news application to use activity streams"""
    name = 'muckrock.news'

    def ready(self):
        """Registers articles with the activity streams plugin"""
        # pylint: disable=invalid-name
        from actstream import registry as action
        from watson import search
        Article = self.get_model('Article')
        action.register(Article)
        search.register(Article.objects.get_published())
