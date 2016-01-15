"""
Middleware for MuckRock
"""

from django.http import HttpResponseRedirect

import hotshot, hotshot.stats
import os
import re
import StringIO
import sys
import tempfile
from urllib import urlencode

from muckrock import settings

class RemoveTokenMiddleware(object):
    """Remove login token from URL"""

    def process_request(self, request):
        """Remove login token from URL"""
        if settings.LOT_MIDDLEWARE_PARAM_NAME in request.GET:
            params = request.GET.copy()
            params.pop(settings.LOT_MIDDLEWARE_PARAM_NAME)
            return HttpResponseRedirect(
                    '%s?%s' % (request.path, urlencode(params)))

# Orignal version taken from http://www.djangosnippets.org/snippets/186/
# Original author: udfalkso
# Modified by: Shwagroo Team and Gun.io

words_re = re.compile( r'\s+' )

group_prefix_re = [
    re.compile( "^.*/django/[^/]+" ),
    re.compile( "^(.*)/[^/]+$" ), # extract module path
    re.compile( ".*" ),           # catch strange entries
]

