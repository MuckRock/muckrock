"""
Sitemap for Q&A application
"""

from django.contrib.sitemaps import Sitemap

from muckrock.qanda.models import Question

class QuestionSitemap(Sitemap):
    """Sitemap for Questions"""

    priority = 0.7
    changefreq = 'weekly'
    limit = 500

    def items(self):
        """Return all questions"""
        return Question.objects.all()

    def lastmod(self, obj):
        """Last modified?"""
        last_answer = obj.answers.last()
        return last_answer.date if last_answer else obj.date

