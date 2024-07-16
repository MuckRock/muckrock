"""
Cache classes that extend S3, for asset compression
"""

# Django
from django.conf import settings
from django.core.files.storage import get_storage_class

# Standard Library
import os

# Third Party
from storages.backends.s3boto3 import S3Boto3Storage

# pylint: disable=abstract-method


class CachedS3Boto3Storage(S3Boto3Storage):
    """
    S3 storage backend for static files that saves the files locally, too.
    """

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage"
        )()

    def save(self, name, content, max_length=None):
        # pylint: disable=protected-access
        self.local_storage._save(name, content)
        super().save(name, self.local_storage._open(name), max_length)
        return name


class OfflineManifestFileStorage(CachedS3Boto3Storage):
    def __init__(self, *args, location=None, **kwargs):
        if location is None:
            location = os.path.join(
                settings.COMPRESS_ROOT, settings.COMPRESS_OUTPUT_DIR
            )
        super().__init__(location, *args, **kwargs)


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
