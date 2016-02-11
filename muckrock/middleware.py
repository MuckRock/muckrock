"""
Middleware for MuckRock
"""

from django.conf import settings
from django.http import HttpResponseRedirect

from urllib import urlencode

class RemoveTokenMiddleware(object):
    """Remove login token from URL"""

    def process_request(self, request):
        """Remove login token from URL"""
        # pylint: disable=no-self-use
        if settings.LOT_MIDDLEWARE_PARAM_NAME in request.GET:
            params = request.GET.copy()
            params.pop(settings.LOT_MIDDLEWARE_PARAM_NAME)
            return HttpResponseRedirect(
                    '%s?%s' % (request.path, urlencode(params)))

