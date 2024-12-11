"""
Celery tasks for mail handling
"""

# Django
from celery import shared_task

# MuckRock
from muckrock.foia.models import FOIACommunication
from muckrock.mailgun import utils


@shared_task(ignore_result=True, name="muckrock.mailgun.tasks.download_links")
def download_links(comm_pk):
    """Download links from the communication"""
    communication = FOIACommunication.objects.get(pk=comm_pk)
    utils.download_links(communication)
