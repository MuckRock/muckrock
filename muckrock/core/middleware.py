# middleware.py
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class FlatpageRedirectMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code == 404:
            site = request.get_host()
            path = request.path_info.lstrip("/")
            redirects = getattr(settings, "FLATPAGES_REDIRECTS", {})
            if site in redirects:
                site_redirects = redirects[site]
                if path in site_redirects:
                    return HttpResponsePermanentRedirect(site_redirects[path])
        return response
