"""
Template tags for Task app
"""

from django.contrib.auth.models import User
from django.template import Library

from muckrock.foia.models import STATUS

register = Library()

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

@register.inclusion_tag('task/stale_agency.html')
def stale_agency(task):
    try:
        task = task.staleagencytask
    except task.DoesNotExist:
        pass
    return {
        'task': task
    }

@register.inclusion_tag('task/flagged.html')
def flagged(task):
    try:
        task = task.flaggedtask
    except task.DoesNotExist:
        pass
    return {
        'task': task
    }

@register.inclusion_tag('task/new_agency.html')
def new_agency(task):
    try:
        task = task.newagencytask
    except task.DoesNotExist:
        pass
    return {
        'task': task
    }

@register.inclusion_tag('task/response.html')
def response(task):
    try:
        task = task.responsetask
    except task.DoesNotExist:
        pass
    return {
        'task': task
    }

@register.inclusion_tag('task/default.html')
def default(task):
    return { 'task': task }
