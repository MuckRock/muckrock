"""
Template tags for Task app
"""

from django.contrib.auth.models import User
from django.template import Library

from muckrock.foia.models import STATUS

@register.inclusion_tag('task/orphan.html')
def orphan(task):
    try:
        task = task.orphantask
    except task.DoesNotExist:
        pass
        # TODO: throw Error and return
    staff_list = User.objects.filter(is_staff=True)
    return {
        'task': task,
        'staff_list': staff_list,
    }

@register.inclusion_tag('task/snail_mail.html')
def snail_mail(task):
    try:
        task = task.snailmailtask
    except task.DoesNotExist:
        pass
        # TODO: throw Error and return
    return {
        'task': task,
        'statuses': STATUS
    }

@register.inclusion_tag('task/rejected_email.html')
def rejected_email(task):
    try:
        task = task.rejectedemailtask
    except task.DoesNotExist:
        pass
        # TODO: throw Error and return
    return {
        'task': task,
    }
