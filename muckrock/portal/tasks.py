"""
Celery tasks for the portal application
"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.db.models import F

# Standard Library
import logging
from datetime import date

# Third Party
import requests

# MuckRock
from muckrock.core.utils import zoho_get
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
    # login based on the day number mod 14, so all requests get logged into once
    # every 14 days without needing to store any additional state
    mod_filter = (date.today() - date.fromordinal(1)).days % 14
    foias = FOIARequest.objects.annotate(mod_id=F('id') % 14).filter(
        status__in=[
            'ack', 'processed', 'appealing', 'fix', 'payment', 'lawsuit'
        ],
        portal__type='foiaonline',
        mod_id=mod_filter,
    )

    def create_flag(foia, msg):
        """Create a flag and log a warning for a failed autologin attempt"""
        logger.warn(
            'FOIAOnline autologin: request %s - %s',
            foia.pk,
            msg,
        )
        FlaggedTask.objects.create(
            text='FOIAOnline autologin failed: {}'.format(msg),
            foia=foia,
            category='foiaonline',
        )

    for foia in foias:
        # check if there is an open ticket
        response = zoho_get(
            'tickets/search', {
                'limit': 1,
                'channel': 'Web',
                'category': 'Flag',
                'subject': 'FOIAOnline*',
                'status': 'Open',
                '_all': '{}-{}'.format(foia.slug, foia.pk),
            }
        )
        if response.status_code == requests.codes.ok:
            # found an existing open ticket
            logger.info(
                'FOIAOnline autologin: request %s has an open zoho ticket, not logging in',
                foia.pk
            )
            continue

        logger.info('FOIAOnline autologin: Logging in for request %s', foia.pk)

        if not foia.portal_password:
            create_flag(foia, 'no portal password set')
            continue

        response = requests.post(
            'https://foiaonline.gov/foiaonline/perform_login',
            data={
                'username': foia.get_request_email(),
                'password': foia.portal_password,
            }
        )
        if bad_msg in response.content:
            create_flag(foia, 'bad password')
        elif lock_msg in response.content:
            create_flag(foia, 'account locked')
        elif good_msg not in response.content:
            create_flag(foia, 'unknown')
        else:
            logger.info(
                'FOIAOnline autologin: request %s login succeeded', foia.pk
            )
