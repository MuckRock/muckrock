"""
Middleware for MuckRock
"""

from django.http import HttpResponseRedirect

from urlauth import middleware
from psycopg2 import OperationalError
import logging
import sys

from muckrock import settings

logger = logging.getLogger(__name__)

class AuthKeyMiddleware(middleware.AuthKeyMiddleware):
    """Override process request to remove url auth key from url after validating"""
    # pylint: disable=R0903

    def process_request(self, request):
        """Redirect to request path without get parameters"""
        try:
            super(AuthKeyMiddleware, self).process_request(request)
            if settings.URLAUTH_AUTHKEY_NAME in request.REQUEST:
                return HttpResponseRedirect(request.path)
        except OperationalError as exc:
            logger.error('Middleware error: %s', exc, exc_info=sys.exc_info())
