"""
Celery tasks for the task application
"""

from django.contrib.auth.models import User

from celery.task import task

from datetime import datetime

from muckrock.foia.models import FOIARequest, FOIACommunication


@task(ignore_result=True, name='muckrock.task.tasks.submit_review_update')
def submit_review_update(foia_pks, reply_text, **kwargs):
    """Submit all the follow ups after updating agency contact information"""
    # pylint: disable=unused-argument
    foias = FOIARequest.objects.filter(pk__in=foia_pks)
    muckrock_staff = User.objects.get(username='MuckrockStaff')
    for foia in foias:
        FOIACommunication.objects.create(
                foia=foia,
                from_user=muckrock_staff,
                to_user=foia.get_to_user(),
                date=datetime.now(),
                response=False,
                communication=reply_text,
                )
        foia.submit(switch=True)
