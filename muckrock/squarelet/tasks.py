"""Celery tasks for squarelet app"""
# Django
from celery.task import task

# Standard Library
import logging
import sys

# Third Party
import requests

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.core.utils import squarelet_get
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)


@task(name='muckrock.squarelet.tasks.pull_data')
def pull_data(type_, uuid, **kwargs):
    """Task to pull data from squarelet"""
    types_url = {
        'user': 'users',
        'organization': 'organizations',
    }
    types_model = {
        'user': Profile,
        'organization': Organization,
    }
    if type_ not in types_url:
        logger.warn('Pull data received invalid type: %s', type_)
        return
    resp = squarelet_get('/api/{}/{}/'.format(types_url[type_], uuid))
    try:
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.warn(
            'Exception during pull data: %s', exc, exc_info=sys.exc_info()
        )
        pull_data.retry(
            args=(type_, uuid),
            kwargs=kwargs,
            exc=exc,
            countdown=2 ** pull_data.request.retries,
        )
    else:
        logger.info('Pull data for: %s %s', type_, uuid)
        model = types_model[type_]
        data = resp.json()
        model.objects.squarelet_update_or_create(uuid, data)
