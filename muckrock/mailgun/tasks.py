"""
Celery tasks for mail handling
"""

# Django
from celery import shared_task
from django.conf import settings

# Standard Library
import logging

# MuckRock
from muckrock.foia.models import FOIACommunication
from muckrock.mailgun import utils

logger = logging.getLogger(__name__)


@shared_task(
    ignore_result=True,
    name="muckrock.mailgun.tasks.download_links",
    soft_time_limit=int(settings.CELERY_TASK_TIME_LIMIT) - 30,
)
def download_links(comm_pk):
    """Download links from the communication"""
    if not settings.ENABLE_DOWNLOAD_LINKS:
        logger.info("[DL:%s] Link downloads disabled, skipping", comm_pk)
        return
    communication = FOIACommunication.objects.get(pk=comm_pk)
    utils.download_links(communication)
