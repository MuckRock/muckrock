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
        # pylint: disable=no-self-use
        return Question.objects.prefetch_related('answers').all()

    def lastmod(self, obj):
        """Last modified?"""
        # pylint: disable=no-self-use
        answers = list(obj.answers.all())
        return answers[-1].date if answers else obj.date
