"""Model signal handlers for the FOIA applicaiton"""

from django.conf import settings
from django.db.models.signals import pre_save, post_delete

from boto.s3.connection import S3Connection

from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.foia.tasks import upload_document_cloud

def foia_update_embargo(sender, **kwargs):
    """When embargo has possibly been switched, update the document cloud permissions"""
    # pylint: disable=unused-argument
    request = kwargs['instance']
    old_request = request.get_saved()
    # if we are saving a new FOIA Request, there are no docs to update
    if old_request and request.embargo != old_request.embargo:
        access = 'private' if request.embargo else 'public'
        for doc in request.files.all():
            if doc.is_doccloud() and doc.access != access:
                doc.access = access
                doc.save()
                upload_document_cloud.apply_async(args=[doc.pk, True], countdown=3)
    return

def foia_file_delete_s3(sender, **kwargs):
    """Delete file from S3 after the model is deleted"""
    # pylint: disable=unused-argument

    if settings.CLEAN_S3_ON_FOIA_DELETE:
        # only delete if we are using s3
        foia_file = kwargs['instance']

        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        key = bucket.get_key(foia_file.ffile.name)
        if key:
            key.delete()


pre_save.connect(foia_update_embargo, sender=FOIARequest,
                 dispatch_uid='muckrock.foia.signals.embargo')

post_delete.connect(foia_file_delete_s3, sender=FOIAFile,
                    dispatch_uid='muckrock.foia.signals.delete_s3')
