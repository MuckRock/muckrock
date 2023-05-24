"""
Celery tasks for the task application
"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

# Standard Library
import logging
import sys
from io import BytesIO
from random import randint

# Third Party
import boto3
from fpdf import FPDF
from pypdf import PdfMerger, PdfReader
from requests.exceptions import RequestException
from zenpy.lib.exception import APIException, ZenpyException

# MuckRock
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.task.filters import SnailMailTaskFilterSet
from muckrock.task.models import (
    CrowdfundTask,
    FlaggedTask,
    MultiRequestTask,
    NewAgencyTask,
    NewPortalTask,
    OrphanTask,
    PaymentInfoTask,
    PortalTask,
    ResponseTask,
    ReviewAgencyTask,
    SnailMailTask,
    Task,
)
from muckrock.task.pdf import CoverPDF, SnailMailPDF

logger = logging.getLogger(__name__)


@task(ignore_result=True, name="muckrock.task.tasks.submit_review_update")
def submit_review_update(foia_pks, reply_text, **kwargs):
    """Submit all the follow ups after updating agency contact information"""
    foias = FOIARequest.objects.filter(pk__in=foia_pks)
    muckrock_staff = User.objects.get(username="MuckrockStaff")
    for foia in foias:
        FOIACommunication.objects.create(
            foia=foia,
            from_user=muckrock_staff,
            to_user=foia.get_to_user(),
            datetime=timezone.now(),
            response=False,
            communication=reply_text,
        )
        foia.submit(switch=True)


@task(
    ignore_result=True,
    time_limit=900,
    name="muckrock.task.tasks.snail_mail_bulk_pdf_task",
)
def snail_mail_bulk_pdf_task(pdf_name, get, **kwargs):
    """Save a PDF file for all open snail mail tasks"""
    # pylint: disable=too-many-locals
    cover_info = []
    bulk_merger = PdfMerger(strict=False)

    snails = SnailMailTaskFilterSet(
        get,
        queryset=SnailMailTask.objects.filter(resolved=False)
        .order_by("-amount", "communication__foia__agency")
        .preload_pdf(),
    ).qs[:100]

    blank_pdf = FPDF()
    blank_pdf.add_page()
    blank = BytesIO(blank_pdf.output(dest="S").encode("latin-1"))
    for snail in snails.iterator():
        # generate the pdf and merge all pdf attachments
        pdf = SnailMailPDF(
            snail.communication, snail.category, snail.switch, snail.amount
        )
        prepared_pdf, page_count, files, _mail = pdf.prepare()
        cover_info.append((snail, page_count, files))

        if prepared_pdf is not None:
            # append to the bulk pdf
            bulk_merger.append(prepared_pdf)
            # ensure we align for double sided printing
            if PdfReader(prepared_pdf).getNumPages() % 2 == 1:
                blank.seek(0)
                bulk_merger.append(blank)

    # preprend the cover sheet
    cover_pdf = CoverPDF(cover_info)
    cover_pdf.generate()
    if cover_pdf.page % 2 == 1:
        cover_pdf.add_page()
    bulk_merger.merge(0, BytesIO(cover_pdf.output(dest="S").encode("latin-1")))

    bulk_pdf = BytesIO()
    bulk_merger.write(bulk_pdf)
    bulk_pdf.seek(0)

    s3 = boto3.client("s3")
    s3.upload_fileobj(
        bulk_pdf,
        settings.AWS_MEDIA_BUCKET_NAME,
        pdf_name,
        ExtraArgs={"ACL": settings.AWS_DEFAULT_ACL},
    )


@task(ignore_result=True, max_retries=5, name="muckrock.task.tasks.create_ticket")
def create_ticket(flag_pk, **kwargs):
    """Create a ticket from a flag"""
    try:
        flag = FlaggedTask.objects.get(pk=flag_pk)
    except FlaggedTask.DoesNotExist as exc:
        # give database time to sync
        create_ticket.retry(countdown=300, args=[flag_pk], kwargs=kwargs, exc=exc)

    if flag.resolved:
        return

    try:
        if settings.USE_ZENDESK:
            zen_id = flag.create_zendesk_ticket()
            flag.resolve(form_data={"zen_id": zen_id})
    except (RequestException, ZenpyException, APIException) as exc:
        logger.warning("ZenPy error: %s", exc, exc_info=sys.exc_info())
        raise create_ticket.retry(
            countdown=(2**create_ticket.request.retries) * 300 + randint(0, 300),
            args=[flag_pk],
            kwargs=kwargs,
            exc=exc,
        )


@task(
    ignore_result=True, max_retries=5, name="muckrock.task.tasks.create_generic_ticket"
)
def create_generic_ticket(task_pk, task_name, **kwargs):
    """Create a ticket from a task"""
    task_models = {
        task.__name__: task
        for task in [
            SnailMailTask,
            NewAgencyTask,
            ResponseTask,
            OrphanTask,
            PortalTask,
            NewPortalTask,
            PaymentInfoTask,
            ReviewAgencyTask,
            MultiRequestTask,
            CrowdfundTask,
        ]
    }
    model = task_models.get(task_name)

    if not model:
        logger.warning("Create generic ticket: task not found: %s", task_name)
        return

    try:
        task_ = model.objects.get(pk=task_pk)
    except Task.DoesNotExist as exc:
        logger.warning("Create generic ticket: %s", exc, exc_info=sys.exc_info())
        return

    try:
        task_.create_zendesk_ticket()
    except (RequestException, ZenpyException, APIException) as exc:
        logger.warning("ZenPy error: %s", exc, exc_info=sys.exc_info())
        raise create_generic_ticket.retry(
            countdown=(2**create_generic_ticket.request.retries) * 300
            + randint(0, 300),
            args=[task_pk],
            kwargs=kwargs,
            exc=exc,
        )


@periodic_task(
    run_every=crontab(hour=4, minute=0), name="muckrock.task.tasks.cleanup_flags"
)
def cleanup_flags():
    """Find any flags that failed to make it to zoho/zendesk and try again"""
    for flag in FlaggedTask.objects.filter(resolved=False):
        create_ticket.delay(flag.pk)
