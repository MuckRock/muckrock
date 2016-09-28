"""Hosts to set URL confs"""

from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns('',
        host(r'www\.muckrock\.com', settings.ROOT_URLCONF, name='default'),
        host(r'www\.foiamachine\.org:8000',
            'muckrock.foiamachine.urls', name='foiamachine'),
        )
