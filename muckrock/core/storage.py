"""
Cache classes that extend S3, for asset compression
"""

# Django
from django.core.files.storage import get_storage_class

# Third Party
from queued_storage.backends import QueuedStorage
from storages.backends.s3boto3 import S3Boto3Storage

# pylint: disable=abstract-method


class QueuedS3DietStorage(QueuedStorage):
    """
    Use S3 as the "local" storage and image_diet as the "remote"
    Since all files live on S3 we don't need to cache which storage the file is on
    """

    def __init__(
        self,
        *args,
        local="storages.backends.s3boto.S3BotoStorage",
        remote="image_diet.storage.DietStorage",
        remote_options=None,
        **kwargs
    ):
        if remote_options is None:
            remote_options = {"file_overwrite": True}
        super(QueuedS3DietStorage, self).__init__(
            local=local, remote=remote, remote_options=remote_options, *args, **kwargs
        )

    def get_storage(self, name):
        """No need to check cache, just always return local"""
        return self.local


class CachedS3Boto3Storage(S3Boto3Storage):
    """
    S3 storage backend that saves the files locally, too.
    """

    def __init__(self, *args, **kwargs):
        super(CachedS3Boto3Storage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage"
        )()

    def save(self, name, content):
        # pylint: disable=protected-access, arguments-differ
        self.local_storage._save(name, content)
        super(CachedS3Boto3Storage, self).save(name, self.local_storage._open(name))
        return name


class MediaRootS3BotoStorage(S3Boto3Storage):
    file_overwrite = False
