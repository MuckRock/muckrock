"""Celery Tasks for the Mailgun application"""

from celery.task import task

import os
from datetime import datetime

from muckrock.foia.models import FOIAFile, FOIARequest, FOIACommunication
from muckrock.foia.tasks import upload_document_cloud

@task(ignore_result=True, max_retries=3, name='muckrock.mailgun.tasks.upload_file')
def upload_file(foia_pk, comm_pk, file_, sender, **kwargs):
    """Upload a file to attach to a FOIA request"""

    # comm may have just been created, db may need time to sync
    # foia will have been in the db already, no need to check if it exists
    try:
        comm = FOIACommunication.objects.get(pk=comm_pk)
    except FOIACommunication.DoesNotExist, exc:
        # give database time to sync
        upload_file.retry(countdown=300,
                args=[foia_pk, comm_pk, file_, sender],
                kwargs=kwargs, exc=exc)
    foia = FOIARequest.objects.get(pk=foia_pk) if foia_pk else None

    access = 'private' if foia and foia.is_embargo() else 'public'
    source = foia.agency.name if foia and foia.agency else sender

    foia_file = FOIAFile(
            foia=foia,
            comm=comm,
            title=os.path.splitext(file_.name)[0][:70],
            date=datetime.now(),
            source=source[:70],
            access=access)
    foia_file.ffile.save(file_.name[:100].encode('ascii', 'ignore'), file_)
    foia_file.save()
    if foia:
        upload_document_cloud.apply_async(args=[foia_file.pk, False], countdown=3)
