"""
Template filters for the accounts application
"""

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def format_phone(phone):
    """Format a phone number for display"""
    return '(%s) %s-%s' % (phone[0:3], phone[3:6], phone[6:10])
