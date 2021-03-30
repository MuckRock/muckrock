"""Model signal handlers for the FOIA applicaiton"""

# Django
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, pre_save

# Third Party
from documentcloud import DocumentCloud

# MuckRock
from muckrock.core.utils import clear_cloudfront_cache, get_s3_storage_bucket
from muckrock.foia.models import FOIAFile, FOIARequest, OutboundRequestAttachment
from muckrock.foia.tasks import upload_document_cloud


@transaction.atomic
def foia_update_embargo(sender, **kwargs):
    """When embargo has possibly been switched, update the document cloud permissions"""
    # pylint: disable=unused-argument
    request = kwargs["instance"]
    old_request = request.get_saved()
    # if we are saving a new FOIA Request, there are no docs to update
    if old_request and request.embargo != old_request.embargo:
        for doc in request.get_files().get_doccloud():
            transaction.on_commit(lambda doc=doc: upload_document_cloud.delay(doc.pk))


def foia_file_delete_s3(sender, **kwargs):
    """Delete file from S3 after the model is deleted"""
    # pylint: disable=unused-argument

    if settings.CLEAN_S3_ON_FOIA_DELETE:
        # only delete if we are using s3
        foia_file = kwargs["instance"]

        bucket = get_s3_storage_bucket()
        bucket.Object(foia_file.ffile.name).delete()

        clear_cloudfront_cache([foia_file.ffile.name])


def foia_file_delete_dc(sender, **kwargs):
    """Delete file from DocumentCloud after the model is deleted"""
    # pylint: disable=unused-argument

    foia_file = kwargs["instance"]
    if foia_file.doc_id:
        dc_client = DocumentCloud(
            username=settings.DOCUMENTCLOUD_BETA_USERNAME,
            password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
            base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
            auth_uri=f"{settings.SQUARELET_URL}/api/",
        )
        dc_client.documents.delete(foia_file.doc_id)


def attachment_delete_s3(sender, **kwargs):
    """Delete file from S3 after the model is deleted"""
    # pylint: disable=unused-argument

    if settings.CLEAN_S3_ON_FOIA_DELETE:
        # only delete if we are using s3
        attachment = kwargs["instance"]

        bucket = get_s3_storage_bucket()
        bucket.Object(attachment.ffile.name).delete()


pre_save.connect(
    foia_update_embargo,
    sender=FOIARequest,
    dispatch_uid="muckrock.foia.signals.embargo",
)

post_delete.connect(
    foia_file_delete_s3,
    sender=FOIAFile,
    dispatch_uid="muckrock.foia.signals.file_delete_s3",
)

post_delete.connect(
    foia_file_delete_dc,
    sender=FOIAFile,
    dispatch_uid="muckrock.foia.signals.file_delete_dc",
)

post_delete.connect(
    attachment_delete_s3,
    sender=OutboundRequestAttachment,
    dispatch_uid="muckrock.foia.signals.attachment_delete_s3",
)
