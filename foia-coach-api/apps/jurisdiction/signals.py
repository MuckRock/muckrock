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
def upload_resource_to_gemini(sender, instance, created, **kwargs):
    """Automatically upload/update resource in Gemini when saved"""
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
            from apps.jurisdiction.services.gemini_service import (
                GeminiFileSearchService,
            )

            if instance.file and instance.is_active:
                service = GeminiFileSearchService()
                service.upload_resource(instance)
        except Exception as exc:
            logger.error(
                "Error uploading resource to Gemini: %s",
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
def remove_resource_from_gemini(sender, instance, **kwargs):
    """Remove resource from Gemini when deleted"""
    # pylint: disable=unused-argument,import-outside-toplevel,broad-exception-caught
    # Avoid circular import
    try:
        from apps.jurisdiction.services.gemini_service import (
            GeminiFileSearchService,
        )

        if instance.gemini_file_id:
            service = GeminiFileSearchService()
            service.remove_resource(instance)
    except Exception as exc:
        logger.error(
            "Error removing resource from Gemini: %s",
            exc,
            exc_info=sys.exc_info(),
        )
