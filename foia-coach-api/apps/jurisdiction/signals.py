"""
Signal handlers for jurisdiction app
"""

# Standard Library
import logging
import sys

# Django
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

# Local
from apps.jurisdiction.models import JurisdictionResource, ResourceProviderUpload

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ResourceProviderUpload)
def upload_resource_to_provider(sender, instance, created, **kwargs):
    """
    Automatically upload resource to provider when ResourceProviderUpload status is 'pending'.

    This signal triggers when a ResourceProviderUpload record is created or updated
    with index_status='pending', initiating the upload process.
    """
    # pylint: disable=unused-argument,import-outside-toplevel,broad-exception-caught

    # Only upload if status is 'pending' to avoid infinite recursion
    if instance.index_status != 'pending':
        return

    def do_upload():
        """Perform the upload after transaction commits"""
        try:
            # Avoid circular import
            from apps.jurisdiction.services.providers.factory import RAGProviderFactory

            # Update status to 'uploading' using QuerySet.update() to avoid triggering signals
            ResourceProviderUpload.objects.filter(pk=instance.pk).update(
                index_status='uploading',
                updated_at=timezone.now()
            )

            # Get provider and upload
            provider = RAGProviderFactory.get_provider(instance.provider)
            result = provider.upload_resource(instance.resource)

            # Update with success using QuerySet.update() to avoid triggering signals
            ResourceProviderUpload.objects.filter(pk=instance.pk).update(
                provider_file_id=result['file_id'],
                provider_store_id=result['store_id'],
                provider_metadata=result.get('metadata', {}),
                index_status='ready',
                indexed_at=timezone.now(),
                error_message='',
                updated_at=timezone.now()
            )

            logger.info(
                "Successfully uploaded resource %s to %s provider",
                instance.resource_id,
                instance.provider
            )

        except Exception as exc:
            logger.error(
                "Failed to upload resource %s to %s: %s",
                instance.resource_id,
                instance.provider,
                exc,
                exc_info=sys.exc_info(),
            )
            # Update error status using QuerySet.update() to avoid triggering signals
            ResourceProviderUpload.objects.filter(pk=instance.pk).update(
                index_status='error',
                error_message=str(exc)[:1000],
                updated_at=timezone.now()
            )

    # Schedule upload to run after transaction commits
    transaction.on_commit(do_upload)


@receiver(post_delete, sender=ResourceProviderUpload)
def remove_resource_from_provider(sender, instance, **kwargs):
    """
    Remove resource from provider when ResourceProviderUpload is deleted.

    This signal handles cleanup when an upload record is explicitly deleted,
    removing the resource from the provider's file store.
    """
    # pylint: disable=unused-argument,import-outside-toplevel,broad-exception-caught

    # Only try to remove if the upload was successful and we have a file ID
    if not instance.provider_file_id or instance.index_status != 'ready':
        return

    def do_remove():
        """Perform the removal after transaction commits"""
        try:
            # Avoid circular import
            from apps.jurisdiction.services.providers.factory import RAGProviderFactory

            provider = RAGProviderFactory.get_provider(instance.provider)
            provider.remove_resource(instance.resource, instance.provider_file_id)

            logger.info(
                "Successfully removed resource %s from %s provider",
                instance.resource_id,
                instance.provider
            )

        except Exception as exc:
            logger.error(
                "Failed to remove resource from %s: %s",
                instance.provider,
                exc,
                exc_info=sys.exc_info(),
            )

    # Schedule removal to run after transaction commits
    transaction.on_commit(do_remove)
