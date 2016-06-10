"""
Template tags and filters for FOIA requests
"""

from django import template

register = template.Library()

@register.filter
def classify_status(status):
    """Returns a class corresponding to a status"""
    class_stop = 'red'
    class_wait = ''
    class_go = 'green'
    classes = {
        'started': class_wait,
        'submitted': class_wait,
        'ack': class_wait,
        'fix': class_stop,
        'payment': class_stop,
        'rejected': class_stop,
        'no_docs': class_stop,
        'done': class_go,
        'partial': class_go,
        'abandoned': class_stop,
        'appealing': class_wait,
    }
    return classes.get(status, class_wait)
