"""
Cache classes that extend S3, for asset compression
"""

from django.core.files.storage import get_storage_class

from storages.backends.s3boto import S3BotoStorage
from queued_storage.backends import QueuedStorage

# pylint: disable=abstract-method
class CachedS3BotoStorage(S3BotoStorage):
    """
    S3 storage backend that saves the files locally, too.
    via http://django-compressor.readthedocs.org/en/latest/remote-storages/#using-staticfiles
    """
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class("compressor.storage.CompressorFileStorage")()

    # pylint: disable=protected-access
    def save(self, name, content, max_length=None):
        non_gzipped_file_content = content.file
        name = super(CachedS3BotoStorage, self).save(name, content, max_length)
        content.file = non_gzipped_file_content
        self.local_storage._save(name, content)
        return name

    def url(self, name, **kwargs):
        """
        S3 storage backend that sets trailing slash properly
        See:
        http://code.larlet.fr/django-storages/issue/121/s3boto-admin-prefix-issue-with-django-14
        https://gist.github.com/richleland/1324335
        """
        url = super(CachedS3BotoStorage, self).url(name, **kwargs)
        if name.endswith('/') and not url.endswith('/'):
            url += '/'
        return url


class QueuedS3DietStorage(QueuedStorage):
    """
    Use S3 as the "local" storage and image_diet as the "remote"
    Since all files live on S3 we don't need to cache which storage the file is on
    """
    def __init__(self,
            local='django.core.files.storage.FileSystemStorage',
            remote='image_diet.storage.DietStorage',
            remote_options=None,
            *args, **kwargs):
        if remote_options is None:
            remote_options = {'file_overwrite': True}
        super(QueuedS3DietStorage, self).__init__(
                local=local, remote=remote, remote_options=remote_options,
                *args, **kwargs)

    def get_storage(self, name):
        """No need to check cache, just always return local"""
        return self.local
