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

# Local
from apps.jurisdiction.models import JurisdictionResource

logger = logging.getLogger(__name__)


@receiver(post_save, sender=JurisdictionResource)
def upload_resource_to_provider(sender, instance, created, **kwargs):
    """Automatically upload/update resource to configured RAG provider when saved"""
    # pylint: disable=unused-argument,import-outside-toplevel,broad-exception-caught

    # Only upload if status is 'pending' to avoid infinite recursion
    # The upload_resource method will update the status, which would otherwise
    # trigger this signal again
    if instance.index_status != 'pending':
        return

    def do_upload():
        """Perform the upload after transaction commits"""
        try:
            # Avoid circular import
            from apps.jurisdiction.services.providers.helpers import get_provider

            if instance.file and instance.is_active:
                # Get provider for this resource
                provider = get_provider(instance.provider)

                # Upload resource
                result = provider.upload_resource(instance)

                # Update resource with provider metadata
                instance.provider_file_id = result.get('file_id')
                instance.provider_store_id = result.get('store_id')
                instance.provider_metadata = result.get('metadata', {})

                # For backward compatibility: sync to legacy gemini_file_id
                if instance.provider == 'gemini':
                    instance.gemini_file_id = instance.provider_file_id

                # Save is already handled by the provider.upload_resource method
                # which updates index_status and indexed_at

        except Exception as exc:
            logger.error(
                "Error uploading resource to provider %s: %s",
                instance.provider,
                exc,
                exc_info=sys.exc_info(),
            )
            # Update status to error
            JurisdictionResource.objects.filter(pk=instance.pk).update(
                index_status="error"
            )

    # Schedule upload to run after transaction commits
    # This ensures the resource is fully saved before we try to update it
    transaction.on_commit(do_upload)


@receiver(post_delete, sender=JurisdictionResource)
def remove_resource_from_provider(sender, instance, **kwargs):
    """Remove resource from configured RAG provider when deleted"""
    # pylint: disable=unused-argument,import-outside-toplevel,broad-exception-caught
    try:
        # Avoid circular import
        from apps.jurisdiction.services.providers.helpers import get_provider

        # Only try to remove if we have a provider_file_id
        # (or legacy gemini_file_id for backward compatibility)
        if instance.provider_file_id or instance.gemini_file_id:
            provider = get_provider(instance.provider)
            provider.remove_resource(instance)

    except Exception as exc:
        logger.error(
            "Error removing resource from provider %s: %s",
            instance.provider,
            exc,
            exc_info=sys.exc_info(),
        )
