"""
Celery tasks for the dataset application
"""

from django.conf import settings
from django.contrib.auth.models import User
from celery.task import task

from boto.s3.connection import S3Connection
import os.path
from smart_open import smart_open

from muckrock.dataset.models import DataSet

CSV_FILES = ('.csv',)
EXCEL_FILES = ('.xls', '.xlsx')

@task(name='muckrock.dataset.tasks.process_dataset_file')
def process_dataset_file(file_key, user_pk):
    """Generate a dataset from a file stored on S3"""
    base_name = os.path.basename(file_key)
    title, ext = os.path.splitext(base_name)
    if ext not in CSV_FILES + EXCEL_FILES:
        # don't bother continuing if it is an illegal file type
        return
    user = User.objects.get(pk=user_pk)
    conn = S3Connection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
            )
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    key = bucket.get_key(file_key)
    with smart_open(key) as data_file:
        if ext in CSV_FILES:
            DataSet.objects.create_from_csv(title, user, data_file)
        elif ext in EXCEL_FILES:
            DataSet.objects.create_from_xls(title, user, data_file)
