"""
Signal handlers for jurisdiction app
"""

# Standard Library
import logging
import sys

# Django
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

# MuckRock
from muckrock.jurisdiction.models import JurisdictionResource

logger = logging.getLogger(__name__)


@receiver(post_save, sender=JurisdictionResource)
def upload_resource_to_gemini(sender, instance, created, **kwargs):
    """Automatically upload/update resource in Gemini when saved"""
    # pylint: disable=unused-argument,import-outside-toplevel,broad-exception-caught
    # Avoid circular import
    try:
        from muckrock.jurisdiction.services.gemini_service import (
            GeminiFileSearchService,
        )

        if instance.file and instance.is_active:
            service = GeminiFileSearchService()
            service.upload_and_index_resource(instance)
    except Exception as exc:
        logger.error(
            "Error uploading resource to Gemini: %s",
            exc,
            exc_info=sys.exc_info(),
        )
        # Update status to error
        instance.index_status = "error"
        JurisdictionResource.objects.filter(pk=instance.pk).update(index_status="error")


@receiver(post_delete, sender=JurisdictionResource)
def remove_resource_from_gemini(sender, instance, **kwargs):
    """Remove resource from Gemini when deleted"""
    # pylint: disable=unused-argument,import-outside-toplevel,broad-exception-caught
    # Avoid circular import
    try:
        from muckrock.jurisdiction.services.gemini_service import (
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
