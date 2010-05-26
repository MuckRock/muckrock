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

@register.simple_tag
def page_links(page_obj):
    """Return page links for surrounding pages"""

    def make_link(num, skip):
        """Make a link to page num"""
        if num != skip:
            return '<a href="?page=%d">%d</a>' % (num, num)
        else:
            return str(num)

    pages = range(max(page_obj.number - 3, 1),
                  min(page_obj.number + 3, page_obj.paginator.num_pages) + 1)
    links = '&nbsp;&nbsp;'.join(make_link(n, page_obj.number) for n in pages)

    if pages[0] != 1:
        links = '&hellip;&nbsp;' + links
    if pages[-1] != page_obj.paginator.num_pages:
        links += '&nbsp;&hellip;'

    return '%s' % links
