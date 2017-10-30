"""
Sitemap for flatpages
"""

from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site

class FlatPageSitemap(Sitemap):
    """Sitemap for Articles"""

    def items(self):
        """Return all flatpages"""
        site = Site.objects.get(domain='www.muckrock.com')
        return site.flatpage_set.filter(registration_required=False)
