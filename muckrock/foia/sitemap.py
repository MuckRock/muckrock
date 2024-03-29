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
    changefreq = "weekly"
    limit = 500

    def items(self):
        """Return all public FOIA requests except for noindex requests"""
        return (
            FOIARequest.objects.select_related("agency__jurisdiction")
            .exclude(noindex=True)
            .get_public()
            .only(
                "title",
                "slug",
                "agency__jurisdiction__id",
                "agency__jurisdiction__slug",
            )
        )
