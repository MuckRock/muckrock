"""
Miscellanous utilities
"""

import random
import string

from django.template import Context
from django.template.loader_tags import BlockNode, ExtendsNode

#From http://stackoverflow.com/questions/2687173/django-how-can-i-get-a-block-from-a-template

class BlockNotFound(Exception):
    """Block not found exception"""
    pass

def get_node(template, context=Context(), name='subject'):
    """Render one block from a template"""
    for node in template:
        if isinstance(node, BlockNode) and node.name == name:
            return node.render(context)
        elif isinstance(node, ExtendsNode):
            return get_node(node.nodelist, context, name)
    raise BlockNotFound("Node '%s' could not be found in template." % name)

def generate_key(size=6, chars=string.ascii_uppercase + string.digits):
    """Generates a random alphanumeric key"""
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))
