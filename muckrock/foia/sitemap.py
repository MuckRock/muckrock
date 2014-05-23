"""
Sitemap for FOIA application
"""

from django.contrib.sitemaps import Sitemap

from muckrock.foia.models import FOIARequest

class LimitSitemap(Sitemap):
    """Limit Sitemap"""
    limit = 2000

class FoiaSitemap(LimitSitemap):
    """Sitemap for FOIA Requests"""

    priority = 0.7
    changefreq = 'weekly'

    def items(self):
        """Return all public FOIA requests"""
        return FOIARequest.objects.get_public()
