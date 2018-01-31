"""Hosts to set URL confs"""

# Django
from django.conf import settings

# Standard Library
import re

# Third Party
from django_hosts import host, patterns

host_patterns = patterns(
    '',
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
