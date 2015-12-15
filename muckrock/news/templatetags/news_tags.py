"""
Nodes and tags for rendering news widgets
"""
from django import template

register = template.Library()

@register.inclusion_tag('tags/pullquote.html', takes_context=True)
def pullquote(context, text, sharing=True):
    """Template tag to insert a sharable pullquote."""
    return {
        'request': context.request,
        'text': text,
        'sharing': sharing
    }
