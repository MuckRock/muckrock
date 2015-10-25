"""
Sitemap for Jurisdiction application
"""

from django.contrib.sitemaps import Sitemap

from muckrock.jurisdiction.models import Jurisdiction

class JurisdictionSitemap(Sitemap):
    """Sitemap for Jurisdiction Requests"""

    priority = 0.7
    changefreq = 'monthly'
    limit = 200

    def items(self):
        """Return all non hidden Jurisdictions"""
        return Jurisdiction.objects.filter(hidden=False)

