"""Hosts to set URL confs"""

# Django
from django.conf import settings

# Standard Library
import re

# Third Party
from django_hosts import host, patterns
from furl import furl


def make_host(url):
    """Strip the scheme from the URL, and append the port only if it is non-standard"""
    # pylint: disable=redefined-variable-type
    url = furl(url)
    if url.port not in [80, 443]:
        host_name = "{}:{}".format(url.host, url.port)
    else:
        host_name = url.host
    return re.escape(host_name)


host_patterns = patterns(
    "",
    host(make_host(settings.MUCKROCK_URL), settings.ROOT_URLCONF, name="default",),
    host(
        make_host(settings.FOIAMACHINE_URL),
        "muckrock.foiamachine.urls",
        name="foiamachine",
    ),
)
