"""Hosts to set URL confs"""

from django.conf import settings
from django_hosts import patterns, host

import re

host_patterns = patterns('',
    host(
        re.escape(settings.MUCKROCK_URL),
        settings.ROOT_URLCONF,
        name='default',
        ),
    host(
        re.escape(settings.FOIAMACHINE_URL),
        'muckrock.foiamachine.urls',
        name='foiamachine',
        ),
)
