"""
Shared functionality for tasks
"""

# Django
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import now

# Standard Library
import logging
import sys
from datetime import date, datetime
from hashlib import md5
from time import time

# Third Party
import boto3
from botocore.exceptions import ClientError
from documentcloud import DocumentCloud
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.core.models import HomePage
from muckrock.message.email import TemplateEmail

logger = logging.getLogger(__name__)


class AsyncFileDownloadTask:
    """Base behavior for asynchrnously generating large files for downloading

    Subclasses should set:
    self.dir_name - directory where files will be stored on s3
    self.file_name - name of the file
    self.text_template - text template for notification email
    self.html_template - html template for notification email
    self.subject - subject line for notification email
    self.mode - "w" for text (default), "wb" for binary
    """

    mode = "w"

    def __init__(self, user_pk, hash_key):
        self.user = User.objects.get(pk=user_pk)
        self.bucket = settings.AWS_MEDIA_BUCKET_NAME
        today = date.today()
        self.file_key = "{dir_name}/{y:4d}/{m:02d}/{d:02d}/{md5}/{file_name}".format(
            dir_name=self.dir_name,
            file_name=self.file_name,
            y=today.year,
            m=today.month,
            d=today.day,
            md5=md5(
                "{}{}{}{}".format(
                    int(time()), settings.SECRET_KEY, user_pk, hash_key
                ).encode("ascii")
            ).hexdigest(),
        )
        self.key = f"s3://{self.bucket}/{self.file_key}"

    def get_context(self):
        """Get context for the notification email"""

        s3_client = boto3.client("s3")
        user_media_expiration = int(settings.AWS_MEDIA_EXPIRATION_SECONDS)
        user_media_expiration_days = user_media_expiration // (24 * 3600)
        try:
            response = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.AWS_MEDIA_BUCKET_NAME, "Key": self.file_key},
                ExpiresIn=user_media_expiration,
            )
        except ClientError as exc:
            logger.error(exc, exc_info=sys.exc_info())
            return None
        return {
            "presigned_url": response,
            "expiration_in_days": user_media_expiration_days,
        }

    def send_notification(self):
        """Send the user the link to their file"""
        notification = TemplateEmail(
            user=self.user,
            extra_context=self.get_context(),
            text_template=self.text_template,
            html_template=self.html_template,
            subject=self.subject,
        )
        notification.send(fail_silently=False)

    def run(self):
        """Task entry point"""
        with smart_open(
            self.key, self.mode, s3_min_part_size=settings.AWS_S3_MIN_PART_SIZE
        ) as out_file:
            self.generate_file(out_file)

        s3 = boto3.resource("s3")
        obj = s3.ObjectAcl(self.bucket, self.file_key)
        obj.put(ACL=settings.AWS_DEFAULT_ACL)
        self.send_notification()

    def generate_file(self, out_file):
        """Abstract method"""
        raise NotImplementedError("Subclass must override generate_file")


@shared_task(
    ignore_result=True,
    name="muckrock.stats.tasks.fetch_and_load_documentcloud_stats",
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 5},
)
def fetch_and_load_documentcloud_stats():
    """Fetch yesterday's statistics from DocumentCloud."""
    yesterday = (date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info("Fetching DocumentCloud stats for %s", yesterday)

    # Instantiate client with creds
    client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
    )

    # Call statistics endpoint
    resp = client.get(f"statistics?date={yesterday}")
    resp.raise_for_status()
    data = resp.json()

    stats = data["results"][0]

    homepage = HomePage.load()
    homepage.documentcloud_stats = {
        "date": yesterday,
        "total_documents_public": stats.get("total_documents_public"),
        "total_pages_public": stats.get("total_pages_public"),
        "total_notes_public": stats.get("total_notes_public"),
        "updated_at": now().isoformat(),
    }
    homepage.save()

    return homepage.documentcloud_stats
