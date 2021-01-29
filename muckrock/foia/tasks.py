"""Celery Tasks for the FOIA application"""

# pylint: disable=too-many-lines

# Django
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.aggregates.general import StringAgg
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.mail.message import EmailMessage
from django.db import transaction
from django.db.models import DurationField, F
from django.db.models.functions import Cast, Now
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

# Standard Library
import base64
import csv
import json
import logging
import os
import os.path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta
from random import randint
from urllib.parse import quote_plus

# Third Party
import dill as pickle
import lob
import numpy as np
import requests
from boto.s3.connection import S3Connection
from constance import config
from django_mailgun import MailgunAPIError
from documentcloud import DocumentCloud
from documentcloud.exceptions import DocumentCloudError
from phaxio import PhaxioApi
from phaxio.exceptions import PhaxioError
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal
from scipy.sparse import hstack
from zipstream import ZIP_DEFLATED, ZipFile

# MuckRock
from muckrock.communication.models import (
    Check,
    FaxCommunication,
    FaxError,
    MailCommunication,
)
from muckrock.core.models import ExtractDay
from muckrock.core.tasks import AsyncFileDownloadTask
from muckrock.core.utils import read_in_chunks
from muckrock.foia.exceptions import SizeError
from muckrock.foia.models import FOIACommunication, FOIAComposer, FOIAFile, FOIARequest
from muckrock.task.models import (
    PaymentInfoTask,
    ResponseTask,
    ReviewAgencyTask,
    SnailMailTask,
)
from muckrock.task.pdf import LobPDF

foia_url = r"(?P<jurisdiction>[\w\d_-]+)-(?P<jidx>\d+)/(?P<slug>[\w\d_-]+)-(?P<idx>\d+)"

logger = logging.getLogger(__name__)

client = Client(os.environ.get("SENTRY_DSN"))
register_logger_signal(client)
register_signal(client)

lob.api_key = settings.LOB_SECRET_KEY


def authenticate_documentcloud(request):
    """This is just standard username/password encoding"""
    username = settings.DOCUMENTCLOUD_USERNAME.encode()
    password = settings.DOCUMENTCLOUD_PASSWORD.encode()
    auth = base64.encodebytes(b"%s:%s" % (username, password))[:-1]
    request.add_header("Authorization", "Basic %s" % auth.decode())
    return request


@task(
    ignore_result=True,
    time_limit=600,
    name="muckrock.foia.tasks.upload_document_cloud",
    autoretry_for=(DocumentCloudError,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 10},
)
def upload_document_cloud(ffile_pk, **kwargs):
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

    if ffile.dc_legacy and settings.USE_DC_LEGACY:
        upload_document_cloud_legacy(ffile, change, **kwargs)
        return

    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )

    params = {
        "title": ffile.title,
        "source": ffile.source,
        "description": ffile.description,
        "access": ffile.access,
        "original_extension": ffile.get_extension(),
        "data": {},
    }
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
            ffile.doc_id = f"{document.id}-{document.slug}"
            ffile.save()

        transaction.on_commit(
            lambda: set_document_cloud_pages.apply_async(
                args=[ffile.pk], countdown=settings.DOCCLOUD_PROCESSING_WAIT
            )
        )


def upload_document_cloud_legacy(doc, change, **kwargs):
    """Upload a document to legacy Document Cloud"""

    logger.info("Upload Doc Cloud Legacy: %s", doc.pk)

    if not doc.is_doccloud():
        # not a file doc cloud supports, do not attempt to upload
        return

    params = {
        "title": doc.title,
        "source": doc.source,
        "description": doc.description,
        "access": doc.access,
    }
    foia = doc.get_foia()
    if foia:
        params["related_article"] = (
            "https://www.muckrock.com" + doc.get_foia().get_absolute_url()
        )
    if change:
        params["_method"] = "put"
        url = "/documents/%s.json" % quote_plus(doc.doc_id)
    else:
        params["file"] = doc.ffile.url.replace("https", "http", 1)
        url = "/upload.json"

    params = urllib.parse.urlencode(params)
    params = params.encode("utf8")
    request = urllib.request.Request(
        "https://www.documentcloud.org/api/%s" % url, params
    )
    request = authenticate_documentcloud(request)

    try:
        ret = urllib.request.urlopen(request).read()
        if not change:
            info = json.loads(ret)
            doc.doc_id = info["id"]
            doc.save()
            set_document_cloud_pages_legacy.apply_async(args=[doc.pk], countdown=1800)
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        logger.warning("Upload Doc Cloud error: %s %s", url, doc.pk)
        countdown = (2 ** upload_document_cloud.request.retries) * 300 + randint(0, 300)
        upload_document_cloud.retry(
            args=[doc.pk], kwargs=kwargs, exc=exc, countdown=countdown
        )


@task(
    ignore_result=True,
    max_retries=10,
    name="muckrock.foia.tasks.set_document_cloud_pages_legacy",
)
def set_document_cloud_pages_legacy(doc_pk, **kwargs):
    """Get the number of pages from the document cloud server and save it locally"""

    try:
        doc = FOIAFile.objects.get(pk=doc_pk)
    except FOIAFile.DoesNotExist:
        return

    if doc.pages or not doc.is_doccloud() or not doc.doc_id:
        # already has pages set or not a doc cloud, just return
        return

    request = urllib.request.Request(
        "https://www.documentcloud.org/api/documents/%s.json"
        % quote_plus(doc.doc_id.encode("utf-8"))
    )
    request = authenticate_documentcloud(request)

    try:
        ret = urllib.request.urlopen(request).read()
        info = json.loads(ret)
        doc.pages = info["document"]["pages"]
        doc.save()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            # if 404, this doc id is not on document cloud
            # delete the doc_id which will cause it to get reuploaded by retry_stuck_documents
            doc.doc_id = ""
            doc.save()
        else:
            set_document_cloud_pages_legacy.retry(
                args=[doc.pk], countdown=600, kwargs=kwargs, exc=exc
            )
    except urllib.error.URLError as exc:
        set_document_cloud_pages_legacy.retry(
            args=[doc.pk], countdown=600, kwargs=kwargs, exc=exc
        )


class DocumentCloudRetryError(Exception):
    """Custom Error to trigger a retry if the document is not done processing"""


@task(
    ignore_result=True,
    name="muckrock.foia.tasks.set_document_cloud_pages",
    autoretry_for=(DocumentCloudError, DocumentCloudRetryError),
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


@periodic_task(
    run_every=crontab(hour=0, minute=20),
    name="muckrock.foia.tasks.retry_stuck_documents",
)
def retry_stuck_documents():
    """Reupload all document cloud documents which are stuck"""
    docs = FOIAFile.objects.filter(doc_id="").exclude(comm__foia=None).get_doccloud()
    logger.info("Reupload documents, %d documents are stuck", len(docs))
    for doc in docs:
        upload_document_cloud.delay(doc.pk)


@task(
    ignore_result=True, max_retries=10, name="muckrock.foia.tasks.composer_create_foias"
)
def composer_create_foias(composer_pk, contact_info, **kwargs):
    """Create all the foias for a composer"""
    # pylint: disable=unused-argument
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
            logger.info("Creating the foia for agency (%s, %s)", agency.pk, agency.name)
            FOIARequest.objects.create_new(composer=composer, agency=agency)
        # mark all attachments as sent here, after all requests have been sent
        composer.pending_attachments.filter(user=composer.user, sent=False).update(
            sent=True
        )


@task(
    ignore_result=True,
    max_retries=10,
    name="muckrock.foia.tasks.composer_delayed_submit",
)
def composer_delayed_submit(composer_pk, approve, contact_info, **kwargs):
    """Submit a composer to all agencies"""
    # pylint: disable=unused-argument
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
        return

    logger.info("Fetched the composer")
    # the delayed submit is processing,
    # clear the delayed id, it is too late to cancel
    composer.delayed_id = ""
    composer.save()
    logger.info("Saved the composer")
    if approve:
        logger.info("Approving")
        composer.approved(contact_info)
    else:
        logger.info("Creating Multirequest Task")
        composer.multirequesttask_set.create()


@task(ignore_result=True, max_retries=3, name="muckrock.foia.tasks.classify_status")
def classify_status(task_pk, **kwargs):
    """Use a machine learning classifier to predict the communications status"""

    # pylint: disable=too-many-locals

    def get_text_ocr(doc_id):
        """Get the text OCR from document cloud"""
        doc_cloud_url = "http://www.documentcloud.org/api/documents/%s.json"
        resp = requests.get(doc_cloud_url % quote_plus(doc_id.encode("utf-8")))
        try:
            doc_cloud_json = resp.json()
        except ValueError:
            logger.warning("Doc Cloud error for %s: %s", doc_id, resp.content)
            return ""
        if "error" in doc_cloud_json:
            logger.warning(
                "Doc Cloud error for %s: %s", doc_id, doc_cloud_json["error"]
            )
            return ""
        text_url = doc_cloud_json["document"]["resources"]["text"]
        resp = requests.get(text_url)
        return resp.content.decode("utf-8")

    def get_classifier():
        """Load the pickled classifier"""
        with open("muckrock/foia/classifier.pkl", "rb") as pkl_fp:
            return pickle.load(pkl_fp)

    def predict_status(vectorizer, selector, classifier, text, pages):
        """Run the prediction"""
        input_vect = vectorizer.transform([text])
        pages_vect = np.array([pages], dtype=np.float).transpose()
        input_vect = hstack([input_vect, pages_vect])
        input_vect = selector.transform(input_vect)
        probs = classifier.predict_proba(input_vect)[0]
        max_prob = max(probs)
        status = classifier.classes_[list(probs).index(max_prob)]
        return status, max_prob

    def resolve_if_possible(resp_task):
        """Resolve this response task if possible based off of ML setttings"""
        if config.ENABLE_ML and resp_task.status_probability >= config.CONFIDENCE_MIN:
            try:
                ml_robot = User.objects.get(username="mlrobot")
                resp_task.set_status(resp_task.predicted_status)
                resp_task.resolve(ml_robot, {"status": resp_task.predicted_status})
            except User.DoesNotExist:
                logger.error("mlrobot account does not exist")

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

    full_text = resp_task.communication.communication + (" ".join(file_text))
    vectorizer, selector, classifier = get_classifier()

    status, prob = predict_status(
        vectorizer, selector, classifier, full_text, total_pages
    )

    resp_task.predicted_status = status
    resp_task.status_probability = int(100 * prob)

    resolve_if_possible(resp_task)

    resp_task.save()


@task(
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
        send_fax.retry(
            countdown=300,
            args=[comm_id, subject, body, error_count],
            kwargs=kwargs,
            exc=exc,
        )

    # the fax number should always be set before calling this, if it is not
    # it is likely a race condition and we should retry
    if comm.foia.fax is None:
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
                agency=comm.foia.agency, resolved=False
            )
        else:
            logger.error("Send fax error, will retry: %s", exc, exc_info=sys.exc_info())
            send_fax.retry(
                countdown=300,
                args=[comm_id, subject, body, error_count],
                kwargs=kwargs,
                exc=exc,
            )


@periodic_task(
    run_every=crontab(hour=5, minute=0),
    time_limit=10 * 60,
    soft_time_limit=570,
    name="muckrock.foia.tasks.followup_requests",
)
def followup_requests():
    """Follow up on any requests that need following up on"""
    log = []
    # weekday returns 5 for sat and 6 for sun
    is_weekday = date.today().weekday() < 5
    if config.ENABLE_FOLLOWUP and (config.ENABLE_WEEKEND_FOLLOWUP or is_weekday):
        try:
            num_requests = FOIARequest.objects.get_followup().count()
            for foia in FOIARequest.objects.get_followup():
                try:
                    foia.followup()
                    log.append("%s - %d - %s" % (foia.status, foia.pk, foia.title))
                except MailgunAPIError as exc:
                    logger.error(
                        "Mailgun error during followups: %s",
                        exc,
                        exc_info=sys.exc_info(),
                    )
        except SoftTimeLimitExceeded:
            logger.warning(
                "Follow ups did not complete in time. " "Completed %d out of %d",
                num_requests - FOIARequest.objects.get_followup().count(),
                num_requests,
            )

        logger.info("Follow Ups:\n%s", "\n".join(log))


@periodic_task(
    run_every=crontab(hour=6, minute=0), name="muckrock.foia.tasks.embargo_warn"
)
def embargo_warn():
    """Warn users their requests are about to come off of embargo"""
    for foia in FOIARequest.objects.filter(
        embargo=True, permanent_embargo=False, date_embargo=date.today()
    ):
        EmailMessage(
            subject='[MuckRock] Embargo about to expire for FOI Request "{}"'.format(
                foia.title
            ),
            body=render_to_string(
                "text/foia/embargo_will_expire.txt", {"request": foia}
            ),
            from_email="info@muckrock.com",
            to=[foia.user.email],
            bcc=["diagnostics@muckrock.com"],
        ).send(fail_silently=False)


@periodic_task(
    run_every=crontab(hour=0, minute=0), name="muckrock.foia.tasks.embargo_expire"
)
def embargo_expire():
    """Expire requests that have a date_embargo before today"""
    for foia in FOIARequest.objects.filter(
        embargo=True, permanent_embargo=False, date_embargo__lt=date.today()
    ):
        foia.embargo = False
        foia.save(comment="embargo expired")
        EmailMessage(
            subject='[MuckRock] Embargo expired for FOI Request "{}"'.format(
                foia.title
            ),
            body=render_to_string(
                "text/foia/embargo_did_expire.txt", {"request": foia}
            ),
            from_email="info@muckrock.com",
            to=[foia.user.email],
            bcc=["diagnostics@muckrock.com"],
        ).send(fail_silently=False)


# Increase the time limit for autoimport to 10 hours, and a soft time limit to
# 5 minutes before that
@periodic_task(
    run_every=crontab(hour=2, minute=0),
    name="muckrock.foia.tasks.autoimport",
    time_limit=36000,
    soft_time_limit=35700,
)
def autoimport():
    """Auto import documents from S3"""
    # pylint: disable=broad-except
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    p_name = re.compile(
        r"(?P<month>\d\d?)-(?P<day>\d\d?)-(?P<year>\d\d) "
        r"(?P<docs>(?:mr\d+(?: |$))+)",
        re.I,
    )

    def s3_copy(bucket, key_or_pre, dest_name):
        """Copy an s3 key or prefix"""

        if key_or_pre.name.endswith("/"):
            for key in bucket.list(prefix=key_or_pre.name, delimiter="/"):
                if key.name == key_or_pre.name:
                    key.copy(bucket, dest_name)
                    continue
                s3_copy(
                    bucket,
                    key,
                    "%s/%s" % (dest_name, os.path.basename(os.path.normpath(key.name))),
                )
        else:
            key_or_pre.copy(bucket, dest_name)

    def s3_delete(bucket, key_or_pre):
        """Delete an s3 key or prefix"""

        if key_or_pre.name.endswith("/"):
            for key in bucket.list(prefix=key_or_pre.name, delimiter="/"):
                if key.name == key_or_pre.name:
                    key.delete()
                    continue
                s3_delete(bucket, key)
        else:
            key_or_pre.delete()

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
    def import_key(key, storage_bucket, comm, log):
        """Import a key"""

        foia = comm.foia
        file_name = os.path.split(key.name)[1]

        # first parameter is instance, but we do not have one yet
        # luckily, it is only used if the upload_to for the field is
        # a callable, which it is not, so it is safe to pass in None
        full_file_name = FOIAFile.ffile.field.generate_filename(None, file_name)
        full_file_name = default_storage.get_available_name(full_file_name)

        new_key = key.copy(storage_bucket, full_file_name)
        new_key.set_acl("public-read")

        foia_file = comm.attach_file(path=full_file_name, name=file_name, now=False)

        if key.size != foia_file.ffile.size:
            raise SizeError(key.size, foia_file.ffile.size, foia_file)

        log.append(
            "SUCCESS: %s uploaded to FOIA Request %s with a status of %s"
            % (file_name, foia.pk, foia.status)
        )

    def import_prefix(prefix, bucket, storage_bucket, comm, log):
        """Import a prefix (folder) full of documents"""

        for key in bucket.list(prefix=prefix.name, delimiter="/"):
            if key.name == prefix.name:
                continue
            if key.name.endswith("/"):
                log.append(
                    "ERROR: nested directories not allowed: %s in %s"
                    % (key.name, prefix.name)
                )
                continue
            try:
                import_key(key, storage_bucket, comm, log)
            except SizeError as exc:
                s3_copy(bucket, key, "review/%s" % key.name[6:])
                exc.args[2].delete()  # delete the foia file
                comm.delete()
                log.append(
                    "ERROR: %s was %s bytes and after uploaded was %s bytes - retry"
                    % (key.name[6:], exc.args[0], exc.args[1])
                )

    def process(log):
        """Process the files"""
        log.append("Start Time: %s" % timezone.now())
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_AUTOIMPORT_BUCKET_NAME)
        storage_bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        for key in bucket.list(prefix="scans/", delimiter="/"):
            if key.name == "scans/":
                continue
            # strip off 'scans/'
            file_name = key.name[6:]

            try:
                foia_pks, file_datetime = parse_name(file_name)
            except ValueError as exc:
                s3_copy(bucket, key, "review/%s" % file_name)
                s3_delete(bucket, key)
                log.append(str(exc))
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
                        datetime=file_datetime,
                        communication="",
                        hidden=True,
                    )
                    comm.responsetask_set.create(scan=True)
                    MailCommunication.objects.create(
                        communication=comm, sent_datetime=file_datetime
                    )

                    if key.name.endswith("/"):
                        import_prefix(key, bucket, storage_bucket, comm, log)
                    else:
                        import_key(key, storage_bucket, comm, log)

                except FOIARequest.DoesNotExist:
                    s3_copy(bucket, key, "review/%s" % file_name)
                    log.append(
                        "ERROR: %s references FOIA Request %s, but it does not exist"
                        % (file_name, foia_pk)
                    )
                except SoftTimeLimitExceeded:
                    # if we reach the soft time limit,
                    # re-raise so we can catch and clean up
                    raise
                except Exception as exc:
                    s3_copy(bucket, key, "review/%s" % file_name)
                    log.append(
                        "ERROR: %s has caused an unknown error. %s" % (file_name, exc)
                    )
                    logger.error("Autoimport error: %s", exc, exc_info=sys.exc_info())
            # delete key after processing all requests for it
            s3_delete(bucket, key)
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
    finally:
        send_mail(
            "[AUTOIMPORT] %s Logs" % timezone.now(),
            "\n".join(log),
            "info@muckrock.com",
            ["info@muckrock.com"],
            fail_silently=False,
        )


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
            lambda f: f.jurisdiction.parent.name
            if f.jurisdiction.level == "l"
            else f.jurisdiction.name,
            "Jurisdiction State",
        ),
        (lambda f: f.agency.name if f.agency else "", "Agency"),
        (lambda f: f.agency.pk if f.agency else "", "Agency ID"),
        (lambda f: f.date_followup, "Followup Date"),
        (lambda f: f.date_estimate, "Estimated Completion Date"),
        (lambda f: f.composer.requested_docs, "Requested Documents"),
        (lambda f: f.current_tracking_id(), "Tracking Number"),
        (lambda f: f.embargo, "Embargo"),
        (lambda f: f.days_since_submitted, "Days since submitted"),
        (lambda f: f.days_since_updated, "Days since updated"),
        (lambda f: f.project_names, "Projects"),
        (lambda f: f.tag_names, "Tags"),
        (lambda f: f.price, "Price"),
        (lambda f: f.composer.datetime_submitted, "Date Submitted"),
        (lambda f: f.date_due, "Date Due"),
        (lambda f: f.datetime_done, "Date Done"),
    )

    def __init__(self, user_pk, foia_pks):
        super(ExportCsv, self).__init__(
            user_pk, "".join(str(pk) for pk in foia_pks[:100])
        )
        self.foias = (
            FOIARequest.objects.filter(pk__in=foia_pks)
            .select_related("composer__user", "agency__jurisdiction__parent")
            .only(
                "composer__user__username",
                "title",
                "status",
                "slug",
                "agency__jurisdiction__name",
                "agency__jurisdiction__slug",
                "agency__jurisdiction__id",
                "agency__jurisdiction__parent__name",
                "agency__jurisdiction__parent__id",
                "agency__name",
                "agency__id",
                "date_followup",
                "date_estimate",
                "embargo",
                "composer__requested_docs",
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

    def generate_file(self, out_file):
        """Export selected foia requests as a CSV file"""
        writer = csv.writer(out_file)
        writer.writerow(f[1] for f in self.fields)
        for foia in self.foias.iterator():
            writer.writerow(f[0](foia) for f in self.fields)


@task(ignore_result=True, time_limit=1800, name="muckrock.foia.tasks.export_csv")
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
        super(ZipRequest, self).__init__(user_pk, foia_pk)
        self.foia = FOIARequest.objects.get(pk=foia_pk)

    def get_context(self):
        """Add the foia title to the context"""
        context = super(ZipRequest, self).get_context()
        context.update({"foia": self.foia.title})
        return context

    def generate_file(self, out_file):
        """Zip all of the communications and files"""
        with ZipFile(mode="w", compression=ZIP_DEFLATED, allowZip64=True) as zip_file:
            for i, comm in enumerate(self.foia.communications.all()):
                file_name = "{:03d}_{}_comm.txt".format(i, comm.datetime)
                zip_file.writestr(file_name, comm.communication.encode("utf8"))
                for ffile in comm.files.all():
                    zip_file.write_iter(
                        ffile.name(),
                        # read in 5MB chunks at a time
                        read_in_chunks(ffile.ffile, size=5 * 1024 * 1024),
                    )
            for data in zip_file:
                out_file.write(data)


@task(ignore_result=True, time_limit=1800, name="muckrock.foia.tasks.zip_request")
def zip_request(foia_pk, user_pk):
    """Send a user a zip download of their request"""
    ZipRequest(user_pk, foia_pk).run()


@periodic_task(
    run_every=crontab(hour=1, minute=0), name="muckrock.foia.tasks.clean_export_csv"
)
def clean_export_csv():
    """Clean up exported CSVs and request zips that are more than 5 days old"""

    p_csv = re.compile(
        r"(\d{4})/(\d{2})/(\d{2})/[0-9a-f]+/(?:requests?|results)\.(?:csv|zip)"
    )
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    older_than = date.today() - timedelta(5)
    for prefix in ["exported_csv/", "zip_request/"]:
        for key in bucket.list(prefix=prefix):
            file_name = key.name[len(prefix) :]
            m_csv = p_csv.match(file_name)
            if m_csv:
                file_date = date(*(int(i) for i in m_csv.groups()))
                if file_date < older_than:
                    key.delete()


@task(ignore_result=True, max_retries=10, name="muckrock.foia.tasks.foia_send_email")
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
        countdown = (2 ** foia_send_email.request.retries) * 60 + randint(0, 300)
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


@task(
    ignore_result=True,
    max_retries=6,
    rate_limit="15/s",
    name="muckrock.foia.tasks.prepare_snail_mail",
)
def prepare_snail_mail(comm_pk, category, switch, extra, force=False, **kwargs):
    """Determine if we should use Lob or a snail mail task to send this snail mail"""
    # pylint: disable=too-many-locals
    comm = FOIACommunication.objects.get(pk=comm_pk)
    # amount may be a string if it was JSON serialized from a Decimal
    amount = float(extra.get("amount", 0))

    def create_snail_mail_task(reason, error_msg=""):
        """Create a snail mail task for this communication"""
        SnailMailTask.objects.create(
            category=category,
            communication=comm,
            user=comm.from_user,
            switch=switch,
            reason=reason,
            error_msg=error_msg,
            **extra,
        )

    if category == "p":
        address = comm.foia.agency.get_addresses("check").first()
        if address is None:
            PaymentInfoTask.objects.create(communication=comm, amount=amount)
            return
    else:
        address = comm.foia.address

    for test, reason in [
        (not config.AUTO_LOB and not force, "auto"),
        (not address, "addr"),
        (address and address.lob_errors(comm.foia.agency), "badadd"),
        (category == "a" and not config.AUTO_LOB_APPEAL and not force, "appeal"),
        (category == "p" and not config.AUTO_LOB_PAY and not force, "pay"),
        (amount > settings.CHECK_LIMIT and not force, "limit"),
    ]:
        if test:
            create_snail_mail_task(reason)
            return

    pdf = LobPDF(comm, category, switch, amount=amount)
    prepared_pdf, page_count, files, mail = pdf.prepare(address)

    if prepared_pdf:
        # page count will be None if prepare_pdf is None
        total_page_count = page_count + sum(f[2] for f in files)
        file_error = any(f[1] in ("error", "skipped") for f in files)

    for test, reason in [
        (prepared_pdf is None, "pdf"),
        (total_page_count > 12, "page"),
        (file_error, "attm"),
    ]:
        if test:
            create_snail_mail_task(reason)
            return

    # send via lob
    try:
        if category == "p":
            lob_obj = _lob_create_check(comm, prepared_pdf, mail, address, amount)
        else:
            lob_obj = _lob_create_letter(comm, prepared_pdf, mail)
        mail.lob_id = lob_obj.id
        mail.save()
        comm.foia.status = comm.foia.sent_status(category == "a", comm.thanks)
        comm.foia.save()
    except lob.error.APIConnectionError as exc:
        prepare_snail_mail.retry(
            countdown=(2 ** prepare_snail_mail.request.retries) * 300 + randint(0, 300),
            args=[comm_pk, category, switch, extra, force],
            kwargs=kwargs,
            exc=exc,
        )
    except lob.error.LobError as exc:
        logger.error(exc, exc_info=sys.exc_info())
        create_snail_mail_task("lob", exc.args[0])


def _lob_create_letter(comm, prepared_pdf, mail):
    """Send a letter via Lob"""
    return lob.Letter.create(
        description="Letter for communication {}".format(comm.pk),
        to_address=comm.foia.address.lob_format(comm.foia.agency),
        from_address={
            "name": "MuckRock News",
            "company": "DEPT MR {}".format(comm.foia.pk),
            "address_line1": "411A Highland Ave",
            "address_city": "Somerville",
            "address_state": "MA",
            "address_zip": "02144-2516",
        },
        color=False,
        file=prepared_pdf,
        double_sided=True,
        metadata={"mail_id": mail.pk},
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
            "name": "MuckRock News",
            "company": "DEPT MR {}".format(comm.foia.pk),
            "address_line1": "411A Highland Ave",
            "address_city": "Somerville",
            "address_state": "MA",
            "address_zip": "02144-2516",
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
