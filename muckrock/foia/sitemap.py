"""
Sitemap for FOIA application
"""

# Django
from django.contrib.sitemaps import Sitemap

# MuckRock
from muckrock.foia.models import FOIARequest


class FoiaSitemap(Sitemap):
    """Sitemap for FOIA Requests"""

    priority = 0.7
    changefreq = 'weekly'
    limit = 500

    def items(self):
        """Return all public FOIA requests"""
        return FOIARequest.objects.select_related('jurisdiction').get_public()
