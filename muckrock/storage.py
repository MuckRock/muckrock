"""
Custom storage for admin bug
See:
http://code.larlet.fr/django-storages/issue/121/s3boto-admin-prefix-issue-with-django-14
https://gist.github.com/richleland/1324335
"""

from storages.backends.s3boto import S3BotoStorage
 
 
class S3StaticStorage(S3BotoStorage):
    """S3 storage backend that sets trailing slash properly"""
    # pylint: disable=W0223

    def url(self, name):
        url = super(S3StaticStorage, self).url(name)
        if name.endswith('/') and not url.endswith('/'):
            url += '/'
        return url
