"""
Sitemap for Jurisdiction application
"""

from django.contrib.sitemaps import Sitemap

from muckrock.jurisdiction.models import Jurisdiction

class LimitSitemap(Sitemap):
    """Limit Sitemap"""
    limit = 500

class JurisdictionSitemap(LimitSitemap):
    """Sitemap for Jurisdiction Requests"""

    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        """Return all non hidden Jurisdictions"""
        return Jurisdiction.objects.filter(hidden=False)

