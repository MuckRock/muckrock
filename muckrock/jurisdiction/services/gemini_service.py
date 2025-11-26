"""
Gemini File Search Service - Stub for Phase 1

This is a placeholder service that will be fully implemented in Phase 2.
For now, it provides empty methods to satisfy the signal handlers.
"""

# Standard Library
import logging

logger = logging.getLogger(__name__)


class GeminiFileSearchService:
    """Service for managing Gemini File Search integration (stub)"""

    def upload_and_index_resource(self, resource):
        """
        Upload and index a jurisdiction resource (stub)

        This will be implemented in Phase 2 with full Gemini API integration.
        For now, it's a no-op.
        """
        logger.info(
            "Gemini service stub: would upload resource %s "
            "(Phase 2 implementation pending)",
            resource.id,
        )

    def remove_resource(self, resource):
        """
        Remove a resource from Gemini (stub)

        This will be implemented in Phase 2 with full Gemini API integration.
        For now, it's a no-op.
        """
        logger.info(
            "Gemini service stub: would remove resource %s "
            "(Phase 2 implementation pending)",
            resource.id,
        )
