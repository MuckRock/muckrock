"""
Sitemap for Project application
"""

# Django
from django.contrib.sitemaps import Sitemap

# MuckRock
from muckrock.project.models import Project


class ProjectSitemap(Sitemap):
    """Sitemap for Projects"""

    priority = 0.7
    changefreq = 'weekly'
    limit = 500

    def items(self):
        """Return all projects"""
        return Project.objects.order_by('id').get_public()
