"""
Shared functionality for tasks
"""
# Django
from django.conf import settings
from django.contrib.auth.models import User

# Standard Library
from datetime import date
from hashlib import md5
from time import time

# Third Party
from boto.s3.connection import S3Connection
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.message.email import TemplateEmail


class AsyncFileDownloadTask(object):
    """Base behavior for asynchrnously generating large files for downloading

    Subclasses should set:
    self.dir_name - directory where files will be stored on s3
    self.file_name - name of the file
    self.text_template - text template for notification email
    self.html_template - html template for notification email
    self.subject - subject line for notification email
    """

    def __init__(self, user_pk, hash_key):
        self.user = User.objects.get(pk=user_pk)
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        self.bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        today = date.today()
        self.file_key = "{dir_name}/{y:4d}/{m:02d}/{d:02d}/{md5}/{file_name}".format(
            dir_name=self.dir_name,
            file_name=self.file_name,
            y=today.year,
            m=today.month,
            d=today.day,
            md5=md5(
                "{}{}{}{}".format(int(time()), settings.SECRET_KEY, user_pk, hash_key)
            ).hexdigest(),
        )
        self.key = self.bucket.new_key(self.file_key)

    def get_context(self):
        """Get context for the notification email"""
        return {"file": self.file_key}

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
            self.key, "wb", s3_min_part_size=settings.AWS_S3_MIN_PART_SIZE
        ) as out_file:
            self.generate_file(out_file)
        self.key.set_acl("public-read")
        self.send_notification()

    def generate_file(self, out_file):
        """Abstract method"""
        raise NotImplementedError("Subclass must override generate_file")
