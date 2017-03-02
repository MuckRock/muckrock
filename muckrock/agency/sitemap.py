"""
Sitemap for Agency application
"""

from django.contrib.sitemaps import Sitemap

from muckrock.agency.models import Agency

class LimitSitemap(Sitemap):
    """Limit Sitemap"""
    limit = 500

class AgencySitemap(LimitSitemap):
    """Sitemap for Agency Requests"""

    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        """Return all approved Agencies"""
        return Agency.objects.select_related('jurisdiction').get_approved()
