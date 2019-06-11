"""
Celery tasks for the portal application
"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task, task

# Standard Library
import logging
from datetime import date

# Third Party
import requests

# MuckRock
from muckrock.foia.models import FOIARequest
from muckrock.portal.models import Portal
from muckrock.task.models import FlaggedTask

logger = logging.getLogger(__name__)


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


@periodic_task(
    run_every=crontab(hour=3, minute=0),
    name='muckrock.portal.tasks.foiaonline_autologin',
)
def foiaonline_autologin():
    """Automatically login to all open FOIAOnline accounts once every 2 weeks
    to keep accounts active
    """
    bad_msg = 'Either the email address or password is invalid. Please try again.'
    good_msg = 'Your session has been extended for 30 more minutes.'
    lock_msg = 'Your account has been locked, please contact the FOIAonline Help Desk.'
    foias = FOIARequest.objects.filter(
        status__in=[
            'ack', 'processed', 'appealing', 'fix', 'payment', 'lawsuit'
        ],
        portal__type='foiaonline',
    )
    # login based on the day number mod 14, so all requests get logged into once
    # every 14 days without needing to store any additional state
    mod_filter = (date.today() - date.fromordinal(1)).days % 14
    for foia in foias:
        if foia.pk % 14 == mod_filter:
            logger.info(
                'FOIAOnline autologin: Logging in for request %s', foia.pk
            )
            if foia.portal_password:
                response = requests.post(
                    'https://foiaonline.gov/foiaonline/perform_login',
                    data={
                        'username': foia.get_request_email(),
                        'password': foia.portal_password,
                    }
                )
                if bad_msg in response.content:
                    logger.warn(
                        'FOIAOnline autologin: request %s login failed: bad password',
                        foia.pk
                    )
                    FlaggedTask.objects.create(
                        text='FOIAOnline autologin failed: bad password',
                        foia=foia,
                        category='foiaonline',
                    )
                elif lock_msg in response.content:
                    logger.warn(
                        'FOIAOnline autologin: request %s login failed: account locked',
                        foia.pk
                    )
                    FlaggedTask.objects.create(
                        text='FOIAOnline autologin failed: account locked',
                        foia=foia,
                        category='foiaonline',
                    )
                elif good_msg not in response.content:
                    logger.warn(
                        'FOIAOnline autologin: request %s login failed: unknown',
                        foia.pk
                    )
                    FlaggedTask.objects.create(
                        text='FOIAOnline autologin failed: unknown',
                        foia=foia,
                        category='foiaonline',
                    )
                else:
                    logger.info(
                        'FOIAOnline autologin: request %s login succeeded',
                        foia.pk
                    )

            else:
                logger.warn(
                    'FOIAOnline autologin: request %s has no portal password set',
                    foia.pk
                )
                FlaggedTask.objects.create(
                    text='FOIAOnline autologin failed: no portal password set',
                    foia=foia,
                    category='foiaonline',
                )
