"""
Celery tasks for the portal application
"""

# Django
from celery.task import task

# MuckRock
from muckrock.portal.models import Portal


@task(name='muckrock.portal.tasks.portal_task')
def portal_task(portal_pk, portal_method, args=None, kwargs=None):
    """Generic portal task to allow you to run portal methods asynchrnously"""
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    portal = Portal.objects.get(pk=portal_pk)
    method = getattr(portal.portal_type, portal_method)
    method(*args, **kwargs)
