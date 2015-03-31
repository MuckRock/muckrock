"""
Template tags for Task app
"""

from django.contrib.auth.models import User
from django.template import Library

from muckrock.foia.models import STATUS
from muckrock.task.models import Task

register = Library()

@register.inclusion_tag('task/orphan.html')
def orphan(task):
    """Renders an orphan task"""
    try:
        task = task.orphantask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
        }
    except Task.DoesNotExist:
        return

@register.inclusion_tag('task/snail_mail.html')
def snail_mail(task):
    """Renders a snail mail task"""
    try:
        task = task.snailmailtask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
            'status': STATUS
        }
    except task.DoesNotExist:
        return

@register.inclusion_tag('task/rejected_email.html')
def rejected_email(task):
    """Renders a rejected email task"""
    try:
        task = task.rejectedemailtask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
        }
    except Task.DoesNotExist:
        return

@register.inclusion_tag('task/stale_agency.html')
def stale_agency(task):
    """Renders a stale agency task"""
    try:
        task = task.staleagencytask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
        }
    except Task.DoesNotExist:
        return

@register.inclusion_tag('task/flagged.html')
def flagged(task):
    """Renders a flagged task"""
    try:
        task = task.flaggedtask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
        }
    except Task.DoesNotExist:
        return

@register.inclusion_tag('task/new_agency.html')
def new_agency(task):
    """Renders a new agency task"""
    try:
        task = task.newagencytask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
        }
    except Task.DoesNotExist:
        return

@register.inclusion_tag('task/response.html')
def response(task):
    """Renders a response task"""
    try:
        task = task.responsetask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
            'status': STATUS
        }
    except task.DoesNotExist:
        return

@register.inclusion_tag('task/generic.html')
def generic(task):
    """Renders a generic task"""
    try:
        task = task.generictask
        return {
            'task': task,
            'staff_list': User.objects.filter(is_staff=True),
        }
    except task.DoesNotExist:
        return

@register.inclusion_tag('task/default.html')
def default(task):
    """Renders any other kinds of tasks"""
    return {
        'task': task,
        'staff_list': User.objects.filter(is_staff=True),
    }
