"""
Middleware for MuckRock
"""

from django.conf import settings
from django.http import HttpResponseRedirect

from urllib import urlencode

from lot import middleware

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


class LOTMiddleware(middleware.LOTMiddleware):
    """Subclass LOT middleware to not log in if already logged in"""

    def process_request(self, request):
        """Return early if already logged in"""
        if request.user.is_authenticated():
            return
        super(LOTMiddleware, self).process_request(request)
