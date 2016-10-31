"""Hosts to set URL confs"""

from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'www\.muckrock\.com', settings.ROOT_URLCONF, name='default'),
    host(r'%s' % settings.FOIAMACHINE_URL,
        'muckrock.foiamachine.urls', name='foiamachine'),
)
