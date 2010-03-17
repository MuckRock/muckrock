"""
General temaplate tags
"""

import re
from django import template

register = template.Library()

@register.simple_tag
def active(request, pattern):
    """Check url against pattern to determine active css attribute"""
    pattern = pattern.replace('{{user}}', str(request.user))
    if re.search(pattern, request.path):
        return 'current-tab'
    return ''

