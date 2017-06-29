"""
WSGI config for muckrock project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/{{ docs_version }}/howto/deployment/wsgi/
"""

# pylint: disable=wrong-import-position
# pylint: disable=ungrouped-imports
from django.conf import settings
import stackimpact
agent = stackimpact.start(
        agent_key='cbf99eee1c7efe5e054f50b9ee40e88f6b0b2c18',
        app_name=settings.MUCKROCK_URL,
        )

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Fix django closing connection to MemCachier after every request (#11331)
from django.core.cache.backends.memcached import BaseMemcachedCache
BaseMemcachedCache.close = lambda self, **kwargs: None
