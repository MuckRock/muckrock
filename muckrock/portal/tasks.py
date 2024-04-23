"""
Celery tasks for the portal application
"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.db.models import F

# Standard Library
import logging
from datetime import date

# Third Party
import requests
from zenpy import Zenpy

# MuckRock
from muckrock.core.utils import zoho_get
from muckrock.foia.models import FOIARequest
from muckrock.portal.models import Portal
from muckrock.task.models import FlaggedTask

logger = logging.getLogger(__name__)


@task(name="muckrock.portal.tasks.portal_task")
def portal_task(portal_pk, portal_method, args=None, kwargs=None):
    """Generic portal task to allow you to run portal methods asynchrnously"""
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    portal = Portal.objects.get(pk=portal_pk)
    method = getattr(portal.portal_type, portal_method)
    method(*args, **kwargs)
