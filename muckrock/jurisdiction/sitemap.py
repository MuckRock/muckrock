"""
Sitemap for Jurisdiction application
"""

# Django
from django.contrib.sitemaps import Sitemap

# MuckRock
from muckrock.jurisdiction.models import Jurisdiction


class JurisdictionSitemap(Sitemap):
    """Sitemap for Jurisdiction Requests"""

    priority = 0.7
    changefreq = 'monthly'
    limit = 500

    def items(self):
        """Return all non hidden Jurisdictions"""
        return Jurisdiction.objects.select_related('parent__parent').filter(
            hidden=False
        )
