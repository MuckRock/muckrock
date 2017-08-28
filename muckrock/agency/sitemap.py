"""
Sitemap for Agency application
"""

from django.contrib.sitemaps import Sitemap

from muckrock.agency.models import Agency


class AgencySitemap(Sitemap):
    """Sitemap for Agency Requests"""

    priority = 0.7
    changefreq = 'monthly'
    limit = 500

    def items(self):
        """Return all approved Agencies"""
        return (Agency.objects
                .order_by('id')
                .select_related('jurisdiction')
                .get_approved()
                )
