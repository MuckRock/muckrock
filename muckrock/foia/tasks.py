"""Celery Tasks for the FOIA application"""

# pylint: disable=too-many-lines

# Django
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates.general import StringAgg
from django.core.files.storage import default_storage
from django.core.mail.message import EmailMessage
from django.db import transaction
from django.db.models import DurationField, F
from django.db.models.functions import Cast, Now
from django.db.models.query import Prefetch
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

# Standard Library
import asyncio
import csv
import logging
import os
import os.path
import re
import sys
from datetime import date, datetime, time
from random import randint

# Third Party
import boto3
import lob
import requests
from anymail.exceptions import AnymailError
from constance import config
from documentcloud import DocumentCloud
from documentcloud.constants import BULK_LIMIT
from documentcloud.exceptions import DocumentCloudError
from documentcloud.toolbox import grouper
from phaxio import PhaxioApi
from phaxio.exceptions import PhaxioError
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal
from zipstream import ZIP_DEFLATED, ZipFile

# MuckRock
from muckrock.communication.models import (
    Check,
    EmailCommunication,
    FaxCommunication,
    FaxError,
    MailCommunication,
    PortalCommunication,
)
from muckrock.core.models import ExtractDay
from muckrock.core.tasks import AsyncFileDownloadTask
from muckrock.core.utils import read_in_chunks, squarelet_get
from muckrock.foia.exceptions import SizeError
from muckrock.foia.models import (
    FOIACommunication,
    FOIAComposer,
    FOIAFile,
    FOIARequest,
    RawEmail,
)
from muckrock.gloo.app.process_request import RequestStatus, process_request
from muckrock.task.models import ResponseTask, ReviewAgencyTask, SnailMailTask
from muckrock.task.pdf import LobPDF

foia_url = r"(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)"

logger = logging.getLogger(__name__)

client = Client(os.environ.get("SENTRY_DSN"))
register_logger_signal(client)
register_signal(client)

lob.api_key = settings.LOB_SECRET_KEY


@shared_task(
    ignore_result=True,
    time_limit=600,
    name="muckrock.foia.tasks.upload_document_cloud",
    autoretry_for=(DocumentCloudError, requests.ReadTimeout),
    retry_backoff=60,
    retry_kwargs={"max_retries": 10},
)
def upload_document_cloud(ffile_pk):
    """Upload a document to Document Cloud"""

    logger.info("Upload Doc Cloud: %s", ffile_pk)

    ffile = (
        FOIAFile.objects.filter(pk=ffile_pk)
        .select_related("comm__foia__agency__jurisdiction")
        .first()
    )

    if not ffile.is_doccloud():
        # not a file doc cloud supports, do not attempt to upload
        return

    # if it has a doc_id already, we are changing it, not creating it
    change = bool(ffile.doc_id)

    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )

    _upload_documentcloud(
        dc_client,
        ffile,
        change,
        save_doc_attrs=True,
        extra_params={"revision_control": True},
    )


@shared_task(
    ignore_result=True,
    time_limit=600,
    name="muckrock.foia.tasks.upload_user_document_cloud",
    autoretry_for=(DocumentCloudError, requests.exceptions.RequestException),
    retry_backoff=60,
    retry_kwargs={"max_retries": 10},
)
def upload_user_document_cloud(ffile_pk, user_pk):
    """Upload a document to a user's Document Cloud account"""

    logger.info("Upload User Doc Cloud: %s", ffile_pk)
    ffile = (
        FOIAFile.objects.filter(pk=ffile_pk)
        .select_related(
            "comm__foia__agency__jurisdiction",
            "comm__foia__composer__user",
        )
        .first()
    )
    user = User.objects.get(pk=user_pk)

    if not ffile.is_doccloud():
        # not a file doc cloud supports, do not attempt to upload
        return

    try:
        resp = squarelet_get(f"/api/refresh_tokens/{user.profile.uuid}/")
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.warning(
            "Error getting token for Add-On: %s", exc, exc_info=sys.exc_info()
        )
        raise

    dc_client = DocumentCloud(
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )
    dc_client.session.headers.update(
        {"Authorization": "Bearer {}".format(resp.json()["access_token"])}
    )
    project, _created = dc_client.projects.get_or_create_by_title("MuckRock Imports")
    params = {"project": project.id}

    _upload_documentcloud(
        dc_client,
        ffile,
        change=False,
        save_doc_attrs=False,
        extra_params=params,
    )


def _upload_documentcloud(dc_client, ffile, change, save_doc_attrs, extra_params=None):
    """Shared function for uploading to Document Cloud"""
    params = {
        "title": ffile.title,
        "source": ffile.source,
        "description": ffile.description,
        "access": ffile.access,
        "original_extension": ffile.get_extension(),
        "data": {},
    }
    if extra_params:
        params.update(extra_params)
    foia = ffile.get_foia()
    if foia:
        params["data"] = {
            "_mr_request": str(ffile.comm.foia.pk),
            "_mr_agency": str(ffile.comm.foia.agency.pk),
            "_mr_jurisdiction": str(ffile.comm.foia.agency.jurisdiction.pk),
        }
    if ffile.comm and ffile.comm.status:
        params["data"]["_mr_status"] = ffile.comm.get_status_display()
    if foia:
        params["related_article"] = (
            settings.MUCKROCK_URL + ffile.get_foia().get_absolute_url()
        )

    with transaction.atomic():
        if change:
            document = dc_client.documents.get(ffile.doc_id)
            for attr, value in params.items():
                setattr(document, attr, value)
            document.save()
        else:
            document = dc_client.documents.upload(ffile.ffile.url, **params)
            if save_doc_attrs:
                ffile.doc_id = f"{document.id}-{document.slug}"
                ffile.save()

        if save_doc_attrs:
            transaction.on_commit(
                lambda: set_document_cloud_pages.apply_async(
                    args=[ffile.pk], countdown=settings.DOCCLOUD_PROCESSING_WAIT
                )
            )


class DocumentCloudRetryError(Exception):
    """Custom Error to trigger a retry if the document is not done processing"""


@shared_task(
    ignore_result=True,
    name="muckrock.foia.tasks.set_document_cloud_pages",
    autoretry_for=(DocumentCloudError, DocumentCloudRetryError, requests.ReadTimeout),
    retry_backoff=60,
    retry_kwargs={"max_retries": 10},
)
def set_document_cloud_pages(ffile_pk):
    """Get the number of pages from the document cloud server and save it locally"""

    try:
        ffile = FOIAFile.objects.get(pk=ffile_pk)
    except FOIAFile.DoesNotExist:
        return

    if ffile.pages or not ffile.is_doccloud() or not ffile.doc_id:
        # already has pages set or not a doc cloud, just return
        return

    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )
    document = dc_client.documents.get(ffile.doc_id)

    if document.status == "success":
        # the document was processed succsefully, save the page count
        ffile.pages = document.page_count
        ffile.save()
    elif document.status in ("pending", "readable", "nofile"):
        # the document is still processing or downloading the file,
        # retry with exponential backoff
        raise DocumentCloudRetryError()
    elif document.status == "error":
        # if there was an error, try to reprocess the document, then retry
        # setting the pages
        document.process()
        raise DocumentCloudRetryError()


@shared_task
def retry_stuck_documents():
    """Reupload all document cloud documents which are stuck"""
    docs = FOIAFile.objects.filter(doc_id="").exclude(comm__foia=None).get_doccloud()
    logger.info("Reupload documents, %d documents are stuck", len(docs))
    for doc in docs:
        upload_document_cloud.delay(doc.pk)


@shared_task(
    ignore_results=True,
    name="muckrock.foia.tasks.noindex_documentcloud",
    autoretry_for=(DocumentCloudError, requests.ReadTimeout),
    retry_backoff=60,
    retry_kwargs={"max_retries": 10},
)
def noindex_documentcloud(foia_pk):
    """Set the documents for this request to noindex on DocumentCloud"""
    foia = FOIARequest.objects.get(pk=foia_pk)
    doc_ids = foia.get_files().exclude(doc_id="").values_list("doc_id", flat=True)
    # get just the numeric ID
    doc_ids = [d.split("-")[0] for d in doc_ids]
    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )
    for group in grouper(doc_ids, BULK_LIMIT):
        resp = dc_client.patch(
            "documents/",
            json=[{"id": d, "noindex": True} for d in group if d is not None],
        )
        resp.raise_for_status()


@shared_task(
    ignore_result=True, max_retries=10, name="muckrock.foia.tasks.composer_create_foias"
)
def composer_create_foias(composer_pk, contact_info, no_proxy, **kwargs):
    """Create all the foias for a composer"""
    composer = FOIAComposer.objects.get(pk=composer_pk)
    logger.info(
        "Starting composer_create_foias: (%s, %s, %s)",
        composer_pk,
        contact_info,
        composer.agencies.count(),
    )
    with transaction.atomic():
        for agency in composer.agencies.select_related(
            "jurisdiction__law", "jurisdiction__parent__law"
        ).iterator():
            logger.info(
                "Creating the foia for agency (%s, %s, %s)",
                composer_pk,
                agency.pk,
                agency.name,
            )
            FOIARequest.objects.create_new(composer, agency, no_proxy, contact_info)
        # mark all attachments as sent here, after all requests have been sent
        composer.pending_attachments.filter(user=composer.user, sent=False).update(
            sent=True
        )


@shared_task(max_retries=10, name="muckrock.foia.tasks.composer_delayed_submit")
def composer_delayed_submit(composer_pk, approve, contact_info, **kwargs):
    """Submit a composer to all agencies"""
    logger.info(
        "Starting composer_delayed_submit: (%s, %s, %s, %s)",
        composer_pk,
        approve,
        contact_info,
        kwargs,
    )
    try:
        composer = FOIAComposer.objects.get(pk=composer_pk)
    except FOIAComposer.DoesNotExist:
        # If the composer was deleted, just return
        logger.info("could not fetch composer %s from db", composer_pk)
        return

    logger.info("Fetched the composer: %s", composer_pk)
    # the delayed submit is processing,
    # clear the delayed id, it is too late to cancel
    composer.delayed_id = ""
    composer.save()
    logger.info("Saved the composer: %s", composer_pk)
    if approve:
        logger.info("Approving: %s", composer_pk)
        composer.approved(contact_info)
    else:
        logger.info("Creating Multirequest Task: %s", composer_pk)
        composer.multirequesttask_set.create()


def get_text_ocr(doc_id):
    """Get the text OCR from document cloud"""

    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )

    try:
        document = dc_client.documents.get(doc_id)
    except DocumentCloudError as exc:
        logger.warning("Doc Cloud error for %s: %s", doc_id, exc.error)
        return ""

    return document.full_text


def resolve_gloo_if_possible(resp_task, extracted_data):
    """Resolve this response task if possible based off of ML setttings"""

    # do not resolve the task if gloo is disabled for the request
    if resp_task.communication.foia.disable_gloo:
        return

    # do not resolve the task if gloo cannot determine the correct status
    if resp_task.predicted_status == "indeterminate":
        return

    # do not resolve the task if gloo classifies a communication as completed
    # or partially completed without an attachment
    if (
        resp_task.predicted_status in ["done", "partial"]
        and not resp_task.communication.files.exists()
    ):
        return

    # do not resolve the task if gloo detects payments, to avoid false positives
    if (
        not config.GLOO_RESOLVE_PAYMENTS
        and extracted_data.requestStatus == RequestStatus.PAYMENT_REQUIRED
    ):
        return

    try:
        gloo_robot = User.objects.get(username="gloo")
        values = {"status": resp_task.predicted_status}
        resp_task.set_status(resp_task.predicted_status)
        if extracted_data.trackingNumber:
            values["tracking_id"] = extracted_data.trackingNumber
            resp_task.set_tracking_id(extracted_data.trackingNumber)
        if extracted_data.price:
            values["price"] = extracted_data.price
            resp_task.set_price(extracted_data.price)
        if extracted_data.dateEstimate:
            try:
                resp_task.set_date_estimate(
                    datetime.strptime(extracted_data.dateEstimate, "%Y-%m-%d").date()
                )
                values["date_estimate"] = extracted_data.dateEstimate
            except ValueError:
                # ignore the date estimate if it is the wrong format
                pass

        resp_task.resolve(gloo_robot, values)
    except User.DoesNotExist:
        logger.error("gloo account does not exist")


@shared_task(
    ignore_result=True, max_retries=3, name="muckrock.foia.tasks.classify_status"
)
def classify_status(task_pk, **kwargs):
    """Use a machine learning classifier to predict the communications status"""

    try:
        resp_task = ResponseTask.objects.get(pk=task_pk)
    except ResponseTask.DoesNotExist as exc:
        classify_status.retry(countdown=60 * 30, args=[task_pk], kwargs=kwargs, exc=exc)

    file_text = []
    total_pages = 0
    for file_ in resp_task.communication.files.all():
        total_pages += file_.pages
        if file_.is_doccloud() and file_.doc_id:
            file_text.append(get_text_ocr(file_.doc_id))
        elif file_.is_doccloud() and not file_.doc_id:
            # wait longer for document cloud
            classify_status.retry(countdown=60 * 30, args=[task_pk], kwargs=kwargs)

    # new classify
    if config.ENABLE_GLOO:
        try:
            extracted_data, status = asyncio.run(
                process_request(
                    resp_task.communication.communication,
                    "\n\n".join(file_text),
                    task_url=settings.MUCKROCK_URL + resp_task.get_absolute_url(),
                    request_url=settings.MUCKROCK_URL
                    + resp_task.communication.foia.get_absolute_url(),
                    agency=str(resp_task.communication.foia.agency),
                    jurisdiction=str(resp_task.communication.foia.agency.jurisdiction),
                )
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Gloo error: %s", exc, exc_info=sys.exc_info())
            status = "indeterminate"
            extracted_data = None

        if config.USE_GLOO:
            resp_task.predicted_status = status
            resolve_gloo_if_possible(resp_task, extracted_data)
            resp_task.save()


@shared_task(
    ignore_result=True,
    max_retries=5,
    name="muckrock.foia.tasks.send_fax",
    rate_limit="15/m",
)
def send_fax(comm_id, subject, body, error_count, **kwargs):
    """Send a fax using the Phaxio API"""
    api = PhaxioApi(settings.PHAXIO_KEY, settings.PHAXIO_SECRET, raise_errors=True)

    try:
        comm = FOIACommunication.objects.get(pk=comm_id)
    except FOIACommunication.DoesNotExist as exc:
        logger.info("send_fax: retry for missing comm")
        send_fax.retry(
            countdown=10,
            args=[comm_id, subject, body, error_count],
            kwargs=kwargs,
            exc=exc,
        )

    # the fax number should always be set before calling this, if it is not
    # it is likely a race condition and we should retry
    if comm.foia.fax is None:
        logger.info("send_fax: retry for missing fax")
        send_fax.retry(
            countdown=300, args=[comm_id, subject, body, error_count], kwargs=kwargs
        )

    files = [f.ffile for f in comm.files.all()]
    callback_url = "{}{}".format(settings.MUCKROCK_URL, reverse("phaxio-callback"))

    fax = FaxCommunication.objects.create(
        communication=comm, sent_datetime=timezone.now(), to_number=comm.foia.fax
    )
    try:
        results = api.send(
            to=comm.foia.fax.as_e164,
            header_text=subject[:45],
            string_data=body,
            string_data_type="text",
            files=files,
            batch=True,
            batch_delay=settings.PHAXIO_BATCH_DELAY,
            batch_collision_avoidance=True,
            callback_url=callback_url,
            **{"tag[fax_id]": fax.pk, "tag[error_count]": error_count},
        )
        fax.fax_id = results["faxId"]
        fax.save()
    except PhaxioError as exc:
        FaxError.objects.create(
            fax=fax,
            datetime=timezone.now(),
            recipient=comm.foia.fax,
            error_type="apiError",
            error_code=exc.args[0],
        )
        fatal_errors = {
            "Phone number is not formatted correctly or invalid. "
            "Please check the number and try again.",
            "Phone number is not permitted.",
        }
        if exc.args[0] in fatal_errors:
            comm.foia.fax.status = "error"
            comm.foia.fax.save()
            ReviewAgencyTask.objects.ensure_one_created(
                agency=comm.foia.agency, resolved=False, source="fax"
            )
        else:
            logger.error("Send fax error, will retry: %s", exc, exc_info=sys.exc_info())
            send_fax.retry(
                countdown=300,
                args=[comm_id, subject, body, error_count],
                kwargs=kwargs,
                exc=exc,
            )


@shared_task
def followup_requests():
    """Follow up on any requests that need following up on"""
    log = []
    # weekday returns 5 for sat and 6 for sun
    is_weekday = date.today().weekday() < 5
    if config.ENABLE_FOLLOWUP and (config.ENABLE_WEEKEND_FOLLOWUP or is_weekday):
        num_requests = FOIARequest.objects.get_followup().count()
        try:
            for foia in FOIARequest.objects.get_followup():
                try:
                    foia.followup()
                    log.append("%s - %d - %s" % (foia.status, foia.pk, foia.title))
                except AnymailError as exc:
                    logger.error(
                        "Mailgun error during followups: %s",
                        exc,
                        exc_info=sys.exc_info(),
                    )
        except SoftTimeLimitExceeded:
            logger.warning(
                "Follow ups did not complete in time. Completed %d out of %d",
                num_requests - FOIARequest.objects.get_followup().count(),
                num_requests,
            )

        logger.info("Follow Ups:\n%s", "\n".join(log))


@shared_task
def embargo_warn():
    """Warn users their requests are about to come off of embargo"""
    for foia in FOIARequest.objects.filter(
        embargo_status="embargo", date_embargo=date.today()
    ):
        EmailMessage(
            subject='[MuckRock] Embargo about to expire for FOI Request "{}"'.format(
                foia.title
            ),
            body=render_to_string(
                "text/foia/embargo_will_expire.txt", {"request": foia}
            ),
            to=[foia.user.email],
            bcc=[settings.DIAGNOSTIC_EMAIL],
        ).send(fail_silently=False)


@shared_task
def embargo_expire():
    """Expire requests that have a date_embargo before today"""
    for foia in FOIARequest.objects.filter(
        embargo_status="embargo", date_embargo__lt=date.today()
    ):
        foia.embargo_status = "public"
        foia.save(comment="embargo expired")
        EmailMessage(
            subject='[MuckRock] Embargo expired for FOI Request "{}"'.format(
                foia.title
            ),
            body=render_to_string(
                "text/foia/embargo_did_expire.txt", {"request": foia}
            ),
            to=[foia.user.email],
            bcc=[settings.DIAGNOSTIC_EMAIL],
        ).send(fail_silently=False)


@shared_task
def autoimport():
    """Auto import documents from S3"""
    # pylint: disable=broad-except
    # pylint: disable=too-many-statements
    p_name = re.compile(
        r"(?P<month>\d\d?)-(?P<day>\d\d?)-(?P<year>\d\d) "
        r"(?P<docs>(?:mr\d+(?: |$))+)",
        re.I,
    )

    def s3_copy(bucket, key_or_pre, dest_name):
        """Copy an s3 key or prefix"""
        if key_or_pre.endswith("/"):
            for obj in bucket.objects.filter(Prefix=key_or_pre):
                if obj.key == key_or_pre:
                    bucket.Object(dest_name).copy_from(
                        CopySource={"Bucket": bucket.name, "Key": obj.key}
                    )
                    continue
                s3_copy(
                    bucket,
                    obj.key,
                    "%s/%s" % (dest_name, os.path.basename(os.path.normpath(obj.key))),
                )
        else:
            bucket.Object(dest_name).copy_from(
                CopySource={"Bucket": bucket.name, "Key": key_or_pre}
            )

    def s3_delete(bucket, key_or_pre):
        """Delete an s3 key or prefix"""
        if key_or_pre.endswith("/"):
            for obj in bucket.objects.filter(Prefix=key_or_pre):
                if obj.key == key_or_pre:
                    obj.delete()
                    continue
                s3_delete(bucket, obj.key)
        else:
            bucket.Object(key_or_pre).delete()

    def parse_name(name):
        """Parse a file name"""
        # strip off trailing / and file extension
        name = os.path.normpath(name)
        name = os.path.splitext(name)[0]

        m_name = p_name.match(name)
        if not m_name:
            raise ValueError("ERROR: %s does not match the file name format" % name)
        foia_pks = [pk[2:] for pk in m_name.group("docs").split()]
        file_datetime = datetime.combine(
            datetime(
                int(m_name.group("year")) + 2000,
                int(m_name.group("month")),
                int(m_name.group("day")),
            ),
            time(tzinfo=timezone.get_current_timezone()),
        )

        return foia_pks, file_datetime

    @transaction.atomic
    def import_key(key, bucket, storage_bucket, comm, log):
        """Import a key"""
        foia = comm.foia
        file_name = os.path.split(key)[1]

        # first parameter is instance, but we do not have one yet
        # luckily, it is only used if the upload_to for the field is
        # a callable, which it is not, so it is safe to pass in None
        full_file_name = FOIAFile.ffile.field.generate_filename(None, file_name)
        full_file_name = default_storage.get_available_name(full_file_name)

        new_obj = storage_bucket.Object(full_file_name)
        new_obj.copy_from(
            CopySource={"Bucket": bucket.name, "Key": key}, ACL=settings.AWS_DEFAULT_ACL
        )

        foia_file = comm.attach_file(path=full_file_name, name=file_name, now=False)

        oldfile = bucket.Object(key)
        if oldfile.content_length != foia_file.ffile.size:
            raise SizeError(key.size, foia_file.ffile.size, foia_file)

        log.append(
            "SUCCESS: %s uploaded to FOIA Request %s with a status of %s"
            % (file_name, foia.pk, foia.status)
        )

    def import_prefix(prefix, bucket, storage_bucket, comm, log):
        """Import a prefix (folder) full of documents"""
        for obj in bucket.objects.filter(Prefix=prefix):
            if obj.key == prefix:
                continue
            if obj.key.endswith("/"):
                log.append(
                    "ERROR: nested directories not allowed: %s in %s"
                    % (obj.key, prefix)
                )
                continue
            try:
                import_key(obj.key, bucket, storage_bucket, comm, log)
            except SizeError as exc:
                s3_copy(
                    bucket,
                    obj.key,
                    "review/%s" % obj.key.replace(settings.AWS_AUTOIMPORT_PATH, ""),
                )
                exc.args[2].delete()  # delete the foia file
                comm.delete()
                log.append(
                    "ERROR: %s was %s bytes and after uploaded was %s bytes - retry"
                    % (
                        obj.key.replace(settings.AWS_AUTOIMPORT_PATH, ""),
                        exc.args[0],
                        exc.args[1],
                    )
                )

    def process(log):
        """Process the files"""
        log.append("Start Time: %s" % timezone.now())
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(settings.AWS_AUTOIMPORT_BUCKET_NAME)
        storage_bucket = s3.Bucket(settings.AWS_MEDIA_BUCKET_NAME)
        for obj in bucket.objects.filter(Prefix=settings.AWS_AUTOIMPORT_PATH):
            if obj.key == settings.AWS_AUTOIMPORT_PATH:
                continue
            # strip off 'scans/'
            file_name = obj.key.replace(settings.AWS_AUTOIMPORT_PATH, "")

            try:
                foia_pks, file_datetime = parse_name(file_name)
            except ValueError as exc:
                log.append(str(exc))
                try:
                    s3_copy(bucket, obj.key, "review/%s" % file_name)
                    s3_delete(bucket, obj.key)
                except Exception as exc2:
                    log.append(str(exc2))
                continue

            for foia_pk in foia_pks:
                try:
                    foia = FOIARequest.objects.get(pk=foia_pk)
                    from_user = foia.agency.get_user() if foia.agency else None

                    comm = FOIACommunication.objects.create(
                        foia=foia,
                        from_user=from_user,
                        to_user=foia.user,
                        response=True,
                        datetime=timezone.now(),
                        communication="",
                        hidden=True,
                    )
                    comm.responsetask_set.create(scan=True)
                    MailCommunication.objects.create(
                        communication=comm, sent_datetime=file_datetime
                    )

                    if obj.key.endswith("/"):
                        import_prefix(obj.key, bucket, storage_bucket, comm, log)
                    else:
                        import_key(obj.key, bucket, storage_bucket, comm, log)

                except FOIARequest.DoesNotExist:
                    s3_copy(bucket, obj.key, "review/%s" % file_name)
                    log.append(
                        "ERROR: %s references FOIA Request %s, but it does not exist"
                        % (file_name, foia_pk)
                    )
                except SoftTimeLimitExceeded:
                    # if we reach the soft time limit,
                    # re-raise so we can catch and clean up
                    raise
                except Exception as exc:
                    s3_copy(bucket, obj.key, "review/%s" % file_name)
                    log.append(
                        "ERROR: %s has caused an unknown error. %s" % (file_name, exc)
                    )
                    logger.error("Autoimport error: %s", exc, exc_info=sys.exc_info())
            # delete key after processing all requests for it
            s3_delete(bucket, obj.key)
        log.append("End Time: %s" % timezone.now())

    try:
        log = []
        process(log)
    except SoftTimeLimitExceeded:
        log.append(
            "ERROR: Time limit exceeded, please check folder for "
            "undeleted uploads.  How big of a file did you put in there?"
        )
        log.append("End Time: %s" % timezone.now())
    except Exception as exc:
        log.append(str(exc))
        log.append("End Time: %s" % timezone.now())
    finally:
        EmailMessage(
            subject="[AUTOIMPORT] %s Logs" % timezone.now(),
            body="\n".join(log),
            from_email=settings.SCANS_EMAIL,
            to=[settings.SCANS_SLACK_EMAIL],
            bcc=[settings.DIAGNOSTIC_EMAIL],
        ).send(fail_silently=False)


class ExportCsv(AsyncFileDownloadTask):
    """Export the list of foia requests for the user"""

    dir_name = "exported_csv"
    file_name = "requests.csv"
    text_template = "message/notification/csv_export.txt"
    html_template = "message/notification/csv_export.html"
    subject = "Your CSV Export"
    fields = (
        (lambda f: f.user.username, "User"),
        (lambda f: f.title, "Title"),
        (lambda f: f.get_status_display(), "Status"),
        (lambda f: settings.MUCKROCK_URL + f.get_absolute_url(), "URL"),
        (lambda f: f.jurisdiction.name, "Jurisdiction"),
        (lambda f: f.jurisdiction.pk, "Jurisdiction ID"),
        (lambda f: f.jurisdiction.get_level_display(), "Jurisdiction Level"),
        (
            lambda f: (
                f.jurisdiction.parent.name
                if f.jurisdiction.level == "l"
                else f.jurisdiction.name
            ),
            "Jurisdiction State",
        ),
        (lambda f: f.agency.name if f.agency else "", "Agency"),
        (lambda f: f.agency.pk if f.agency else "", "Agency ID"),
        (
            lambda f: (
                f.agency.addresses.all()[0].zip_code
                if f.agency and f.agency.addresses.all()
                else ""
            ),
            "Agency Zip Code",
        ),
        (lambda f: f.date_followup, "Followup Date"),
        (lambda f: f.date_estimate, "Estimated Completion Date"),
        (lambda f: f.composer.requested_docs, "Requested Documents"),
        (lambda f: f.current_tracking_id(), "Tracking Number"),
        (lambda f: f.embargo_status, "Embargo"),
        (lambda f: f.days_since_submitted, "Days since submitted"),
        (lambda f: f.days_since_updated, "Days since updated"),
        (lambda f: f.project_names, "Projects"),
        (lambda f: f.tag_names, "Tags"),
        (lambda f: f.price, "Price"),
        (lambda f: f.composer.datetime_submitted, "Date Submitted"),
        (lambda f: f.date_due, "Date Due"),
        (lambda f: f.datetime_done, "Date Done"),
    )

    staff_fields = (
        (lambda f: f.get_request_email(), "Request Email"),
        (
            lambda f: (
                f.communications.all()[0].get_delivered()
                if f.communications.all()
                else ""
            ),
            "Initial Communication Delivered",
        ),
        (
            lambda f: (
                f.communications.all()[0].sent_to() if f.communications.all() else ""
            ),
            "Initial Communication Address",
        ),
        (
            lambda f: (
                inbound[0].get_delivered()
                if (inbound := [c for c in f.communications.all() if c.response])
                else ""
            ),
            "First Inbound Communication Delivered",
        ),
        (
            lambda f: (
                inbound[0].sent_from()
                if (inbound := [c for c in f.communications.all() if c.response])
                else ""
            ),
            "First Inbound Communication Address",
        ),
        (
            lambda f: (
                inbound[-1].get_delivered()
                if (inbound := [c for c in f.communications.all() if c.response])
                else ""
            ),
            "Last Inbound Communication Delivered",
        ),
        (
            lambda f: (
                inbound[-1].sent_from()
                if (inbound := [c for c in f.communications.all() if c.response])
                else ""
            ),
            "Last Inbound Communication Address",
        ),
    )

    def __init__(self, user_pk, foia_pks):
        super().__init__(user_pk, "".join(str(pk) for pk in foia_pks[:100]))
        logger.info("[EXPORT CSV] init user: %d foia count: %d", user_pk, len(foia_pks))
        self.foias = (
            FOIARequest.objects.filter(pk__in=foia_pks)
            .select_related("composer__user", "agency__jurisdiction__parent")
            .prefetch_related("tracking_ids", "agency__addresses")
            .only(
                "agency__id",
                "agency__jurisdiction__id",
                "agency__jurisdiction__level",
                "agency__jurisdiction__name",
                "agency__jurisdiction__parent__id",
                "agency__jurisdiction__parent__name",
                "agency__jurisdiction__slug",
                "agency__name",
                "composer__datetime_submitted",
                "composer__requested_docs",
                "composer__user__username",
                "date_due",
                "date_estimate",
                "date_followup",
                "datetime_done",
                "embargo_status",
                "mail_id",
                "price",
                "slug",
                "status",
                "title",
            )
            .annotate(
                days_since_submitted=ExtractDay(
                    Cast(Now() - F("composer__datetime_submitted"), DurationField())
                ),
                days_since_updated=ExtractDay(
                    Cast(Now() - F("datetime_updated"), DurationField())
                ),
                project_names=StringAgg("projects__title", ",", distinct=True),
                tag_names=StringAgg("tags__name", ",", distinct=True),
            )
        )
        if self.user.is_staff:
            self.fields += self.staff_fields
            self.foias = self.foias.prefetch_related(
                "communications__emails",
                Prefetch(
                    "communications__faxes",
                    queryset=FaxCommunication.objects.select_related("to_number"),
                ),
                Prefetch(
                    "communications__mails",
                    queryset=MailCommunication.objects.select_related("to_address"),
                ),
                "communications__web_comms",
                Prefetch(
                    "communications__portals",
                    queryset=PortalCommunication.objects.select_related("portal"),
                ),
            )

    def generate_file(self, out_file):
        """Export selected foia requests as a CSV file"""
        writer = csv.writer(out_file)
        writer.writerow(f[1] for f in self.fields)
        for i, foia in enumerate(self.foias.iterator(chunk_size=500)):
            if i % 2000 == 0:
                logger.info("[EXPORT CSV] foia %d", i)
            writer.writerow(f[0](foia) for f in self.fields)


@shared_task(
    ignore_result=True, time_limit=18000, name="muckrock.foia.tasks.export_csv"
)
def export_csv(foia_pks, user_pk):
    """Export a csv of the selected FOIA requests"""
    ExportCsv(user_pk, foia_pks).run()


class ZipRequest(AsyncFileDownloadTask):
    """Export all communications and files from a foia request"""

    dir_name = "zip_request"
    file_name = "request.zip"
    text_template = "message/notification/zip_request.txt"
    html_template = "message/notification/zip_request.html"
    subject = "Your zip archive of your request"
    mode = "wb"

    def __init__(self, user_pk, foia_pk):
        self.foia = FOIARequest.objects.get(pk=foia_pk)
        self.file_name = f"{self.foia}.zip"
        super().__init__(user_pk, foia_pk)

    def get_context(self):
        """Add the foia title to the context"""
        context = super().get_context()
        context.update({"foia": self.foia.title})
        return context

    def generate_file(self, out_file):
        """Zip all of the communications and files"""

        # https://stackoverflow.com/questions/57165960/error-0x80070057-the-parameter-is-incorrect-when-unzipping-files
        def clean(filename):
            return re.sub('[<>:"/\\\\|?*]', "_", filename)

        with ZipFile(mode="w", compression=ZIP_DEFLATED, allowZip64=True) as zip_file:
            for i, comm in enumerate(self.foia.communications.all()):
                file_name = "{:03d}_{}_comm.txt".format(i, comm.datetime)
                zip_file.writestr(clean(file_name), comm.communication.encode("utf8"))
                for ffile in comm.files.all():
                    zip_file.write_iter(
                        clean(ffile.name()),
                        # read in 5MB chunks at a time
                        read_in_chunks(ffile.ffile, size=5 * 1024 * 1024),
                    )
            for data in zip_file:
                out_file.write(data)


@shared_task(
    ignore_result=True, time_limit=1800, name="muckrock.foia.tasks.zip_request"
)
def zip_request(foia_pk, user_pk):
    """Send a user a zip download of their request"""
    ZipRequest(user_pk, foia_pk).run()


@shared_task(max_retries=10, name="muckrock.foia.tasks.foia_send_email")
def foia_send_email(foia_pk, comm_pk, options, **kwargs):
    """Send outgoing request emails asynchrnously"""
    # We do not want to do this using djcelery-email, as that
    # requires the entire email body be serialized through redis,
    # which could be quite large
    try:
        foia = FOIARequest.objects.get(pk=foia_pk)
        comm = FOIACommunication.objects.get(pk=comm_pk)
        foia.send_delayed_email(comm, **options)
    except IOError as exc:
        countdown = (2**foia_send_email.request.retries) * 60 + randint(0, 300)
        logger.error(
            "foia_send_email error, will retry in %d minutes: %s",
            countdown,
            exc,
            exc_info=sys.exc_info(),
        )
        foia_send_email.retry(
            countdown=countdown,
            args=[foia_pk, comm_pk, options],
            kwargs=kwargs,
            exc=exc,
        )


@shared_task(
    ignore_result=True,
    max_retries=6,
    rate_limit="15/s",
    name="muckrock.foia.tasks.prepare_snail_mail",
)
def prepare_snail_mail(
    comm_pk, switch, extra, certified, force=False, num_msgs=5, **kwargs
):
    """Determine if we should use Lob or a snail mail task to send this snail mail"""
    # pylint: disable=too-many-locals
    comm = FOIACommunication.objects.get(pk=comm_pk)
    # amount may be a string if it was JSON serialized from a Decimal
    amount = float(extra.get("amount", 0))

    def create_snail_mail_task(reason, error_msg=""):
        """Create a snail mail task for this communication"""
        SnailMailTask.objects.create(
            category=comm.category,
            communication=comm,
            user=comm.from_user,
            switch=switch,
            reason=reason,
            error_msg=error_msg,
            **extra,
        )

    if comm.category == "p":
        address = comm.foia.agency.get_addresses("check").first()
        if address is None:
            # this shouldn't happen
            logger.error(
                "Error geting payment address: %s %s %s",
                comm,
                comm.foia,
                comm.foia.agency,
            )
            comm.foia.flaggedtask_set.create(
                text=f"Something went wrong with payment: {comm.foia} "
                "https://www.muckrock.com{comm.foia.get_absolute_url()}"
            )
            return
    else:
        address = comm.foia.address

    if not address:
        comm.foia.set_address(
            appeal=comm.category == "a", contact_info=None, clear=False
        )
        address = comm.foia.address

    for test, reason in [
        (not config.AUTO_LOB and not force, "auto"),
        (not address, "addr"),
        (address and address.lob_errors(comm.foia.agency), "badadd"),
        (comm.category == "a" and not config.AUTO_LOB_APPEAL and not force, "appeal"),
        (comm.category == "p" and not config.AUTO_LOB_PAY and not force, "pay"),
        (amount > settings.CHECK_LIMIT and not force, "limit"),
    ]:
        if test:
            create_snail_mail_task(reason)
            return

    pdf = LobPDF(comm, comm.category, switch, amount=amount)
    prepared_pdf, total_page_count, _files, mail = pdf.prepare(address, num_msgs)

    for test, reason in [
        (prepared_pdf is None, "pdf"),
        (total_page_count > 12, "page"),
    ]:
        if test:
            create_snail_mail_task(reason)
            return

    # send via lob
    try:
        if comm.category == "p":
            lob_obj = _lob_create_check(comm, prepared_pdf, mail, address, amount)
        else:
            lob_obj = _lob_create_letter(comm, prepared_pdf, mail, certified)
        mail.lob_id = lob_obj.id
        mail.save()
        comm.foia.status = comm.foia.sent_status(comm.category == "a", comm.thanks)
        comm.foia.save(comment="sent via lob")
        comm.foia.update()
    except lob.error.APIConnectionError as exc:
        prepare_snail_mail.retry(
            countdown=(2**prepare_snail_mail.request.retries) * 300 + randint(0, 300),
            args=[comm_pk, comm.category, switch, extra, certified, force, num_msgs],
            kwargs=kwargs,
            exc=exc,
        )
    except lob.error.LobError as exc:
        logger.error(exc, exc_info=sys.exc_info())
        create_snail_mail_task("lob", exc.args[0])


def _lob_create_letter(comm, prepared_pdf, mail, certified):
    """Send a letter via Lob"""
    return lob.Letter.create(
        description="Letter for communication {}".format(comm.pk),
        to_address=comm.foia.address.lob_format(comm.foia.agency),
        from_address={
            "name": settings.ADDRESS_NAME,
            "company": settings.ADDRESS_DEPT.format(pk=comm.foia.pk),
            "address_line1": settings.ADDRESS_STREET,
            "address_city": settings.ADDRESS_CITY,
            "address_state": settings.ADDRESS_STATE,
            "address_zip": settings.ADDRESS_ZIP,
        },
        color=False,
        file=prepared_pdf,
        double_sided=True,
        metadata={"mail_id": mail.pk},
        extra_service=certified,
    )


def _lob_create_check(comm, prepared_pdf, mail, check_address, amount):
    """Send a check via Lob"""
    memo = "MR {}".format(comm.foia.pk)
    tracking_number = comm.foia.current_tracking_id()
    if tracking_number:
        old_memo = memo
        memo += " / {}".format(tracking_number)
        if len(memo) > 40:
            memo = old_memo

    check = lob.Check.create(
        description="Check for communication {}".format(comm.pk),
        to_address=check_address.lob_format(comm.foia.agency),
        from_address={
            "name": settings.ADDRESS_NAME,
            "company": settings.ADDRESS_DEPT.format(pk=comm.foia.pk),
            "address_line1": settings.ADDRESS_STREET,
            "address_city": settings.ADDRESS_CITY,
            "address_state": settings.ADDRESS_STATE,
            "address_zip": settings.ADDRESS_ZIP,
        },
        bank_account=settings.LOB_BANK_ACCOUNT_ID,
        amount=amount,
        memo=memo,
        attachment=prepared_pdf,
        metadata={"mail_id": mail.pk},
    )
    mr_check = Check.objects.create(
        number=check.check_number,
        agency=comm.foia.agency,
        amount=amount,
        communication=comm,
        user=User.objects.get(username="MuckrockStaff"),
    )
    mr_check.send_email()
    return check


@shared_task(
    ignore_result=True,
    autoretry_for=(DocumentCloudError, requests.ReadTimeout),
    retry_backoff=60,
    retry_kwargs={"max_retries": 10},
    name="muckrock.foia.tasks.import_doccloud_file",
)
def import_doccloud_file(file_pk):
    """Import a file from DocumentCloud back into MuckRock"""
    try:
        ffile = FOIAFile.objects.get(pk=file_pk)
    except FOIAFile.DoesNotExist:
        return

    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )
    document = dc_client.documents.get(ffile.doc_id)

    ext = ffile.get_extension()
    if ext != "pdf":
        name = ffile.ffile.name[: -len(ext)] + "pdf"
        ffile.ffile.delete(save=False)
        ffile.ffile.name = name
        ffile.save()

    if document.access == "public":
        with ffile.ffile.open("wb") as out_file, requests.get(
            document.pdf_url, stream=True
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=10 * 1024 * 1024):
                out_file.write(chunk)
    else:
        with ffile.ffile.open("wb") as out_file, dc_client.get(
            document.pdf_url, full_url=True, stream=True
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=10 * 1024 * 1024):
                out_file.write(chunk)


@shared_task(
    ignore_result=True,
    autoretry_for=(requests.exceptions.RequestException, ValueError),
    retry_backoff=60,
    retry_kwargs={"max_retries": 10},
    name="muckrock.foia.tasks.fetch_raw_email",
)
def fetch_raw_email(message_id):
    """Asynchrnously fetch the raw email from MailGun servers for the email
    with the given message ID
    """
    emails = EmailCommunication.objects.filter(message_id=message_id, rawemail=None)
    logger.info(
        "Fetching raw emails: message_id: %s, emails: %s",
        message_id,
        ",".join(str(e.pk) for e in emails),
    )
    if emails:
        RawEmail.objects.make_async(emails)
