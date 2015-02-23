"""
FOIA template tags
"""

from django import template
from django.core.urlresolvers import reverse

register = template.Library()

@register.inclusion_tag('tags/crowdfund.html', takes_context=True)
def crowdfund(context, foia):
    endpoint = reverse('foia-contribute', kwargs={
        'jurisdiction': foia.jurisdiction.slug,
        'jidx': foia.jurisdiction.pk,
        'idx': foia.id,
        'slug': foia.slug
    })
    return {
        'user': context['user'],
        'crowdfund': foia.crowdfund,
        'endpoint': endpoint,
    }