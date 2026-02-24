"""
Storage classes that extend S3
"""

# Django
from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage

# Third Party
from storages.backends.s3boto3 import S3Boto3Storage

# pylint: disable=abstract-method


class CachedS3Boto3Storage(S3Boto3Storage):
    """
    S3 storage backend for static files that also saves files locally.
    Files inherit the bucket's public access policy rather than setting per-object ACLs.
    This works with modern AWS S3 security settings that block public ACLs.
    """

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = StaticFilesStorage()

    def save(self, name, content, max_length=None):
        # Save to local storage first
        # pylint: disable=protected-access
        self.local_storage._save(name, content)
        # Then save to S3
        super().save(name, self.local_storage._open(name), max_length)
        return name


class MediaRootS3BotoStorage(S3Boto3Storage):
    """
    S3 storage backend for user-uploaded media files.
    (It may or may not use the same bucket as static files.)
    """

    file_overwrite = False
    bucket_name = settings.AWS_MEDIA_BUCKET_NAME
    querystring_auth = settings.AWS_MEDIA_QUERYSTRING_AUTH
    custom_domain = settings.AWS_MEDIA_CUSTOM_DOMAIN


class PrivateMediaRootS3BotoStorage(MediaRootS3BotoStorage):
    """S3 storage backend that always uploads files as private"""

    default_acl = "private"


class QueuedS3DietStorage:
    """Left here for old migrations to reference"""
