# middleware.py
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class FlatpageRedirectMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code == 404:
            path = request.path_info.lstrip('/')
            redirects = getattr(settings, 'FLATPAGES_REDIRECTS', {})
            if path in redirects:
                return HttpResponsePermanentRedirect(redirects[path])
        return response