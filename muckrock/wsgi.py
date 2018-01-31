"""
WSGI config for muckrock project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/{{ docs_version }}/howto/deployment/wsgi/
"""

# Django
# Fix django closing connection to MemCachier after every request (#11331)
from django.core.cache.backends.memcached import BaseMemcachedCache
# pylint: disable=wrong-import-position
# pylint: disable=ungrouped-imports
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

BaseMemcachedCache.close = lambda self, **kwargs: None
