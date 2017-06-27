"""
Template tags and filters for FOIA requests
"""

from django import template

register = template.Library()

@register.filter
def classify_status(status):
    """Returns a class corresponding to a status"""
    class_stop = 'red'
    class_wait = 'yellow'
    class_go = 'green'
    class_default = ''
    classes = {
        'rejected': class_stop,
        'no_docs': class_stop,
        'abandoned': class_stop,
        'submitted': class_wait,
        'fix': class_wait,
        'payment': class_wait,
        'lawsuit': class_wait,
        'appealing': class_wait,
        'processed': class_wait,
        'ack': class_wait,
        'done': class_go,
        'partial': class_go,
    }
    return classes.get(status, class_default)
