"""
Gemini provider implementation wrapping existing GeminiFileSearchService.
"""
from django.conf import settings
from typing import Optional, Generator, Dict, Any
import logging
import sys

from .base import RAGProviderBase, ProviderError, ProviderConfigError, ProviderAPIError
from ..gemini_service import GeminiFileSearchService

logger = logging.getLogger(__name__)


class GeminiProvider(RAGProviderBase):
    """
    Gemini provider implementation wrapping existing GeminiFileSearchService.

    This provider wraps the existing Gemini File Search service to match
    the RAGProviderBase interface, preserving all existing functionality.
    """

    PROVIDER_NAME = 'gemini'

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Gemini provider"""
        super().__init__(config)

        # Get configuration
        self.api_key = self.config.get('api_key')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not configured")

        self.model = self.config.get('model', 'gemini-1.5-flash')
        self.store_name = self.config.get('store_name', 'StatePublicRecordsStore')
        self.real_api_enabled = self.config.get('real_api_enabled', False)

        if not self.real_api_enabled:
            logger.warning(
                "⚠️  GEMINI_REAL_API_ENABLED is False - Real API calls are DISABLED. "
                "Set GEMINI_REAL_API_ENABLED=true in environment to enable."
            )

        # Initialize the wrapped Gemini service
        self.service = GeminiFileSearchService() if self.real_api_enabled else None

    def _check_api_enabled(self):
        """Check if real API calls are enabled"""
        if not self.real_api_enabled:
            raise ProviderConfigError(
                "Gemini API calls are disabled. "
                "Set GEMINI_REAL_API_ENABLED=true in environment to enable."
            )

    def create_store(self, display_name: str) -> str:
        """Create a new File Search store"""
        self._check_api_enabled()

        try:
            store_name = self.service.create_store(display_name)
            logger.info(f"Created Gemini File Search store: {store_name}")
            return store_name

        except Exception as exc:
            logger.error(
                "Failed to create Gemini File Search store: %s",
                exc,
                exc_info=sys.exc_info()
            )
            raise ProviderAPIError(f"Failed to create File Search store: {exc}")

    def get_or_create_store(self, display_name: Optional[str] = None) -> str:
        """Get existing File Search store or create new one"""
        self._check_api_enabled()

        try:
            # Gemini service uses self.store_name internally
            # If display_name is provided, we'd need to temporarily override it
            # For now, just use the service's configured store
            store_name = self.service.get_or_create_store()
            logger.info(f"Using Gemini File Search store: {store_name}")
            return store_name

        except Exception as exc:
            logger.error(
                "Failed to get or create Gemini File Search store: %s",
                exc,
                exc_info=sys.exc_info()
            )
            raise ProviderAPIError(f"Failed to get or create File Search store: {exc}")

    def upload_resource(self, resource) -> Dict[str, Any]:
        """Upload a resource file to File Search store"""
        self._check_api_enabled()

        try:
            # Note: Status is managed by the signal handler, not here

            # Upload using the wrapped service
            file_id = self.service.upload_resource(resource)

            # Get the store name
            store_name = self.service.store_name

            logger.info(
                f"Uploaded resource {resource.id} to Gemini File Search store: {file_id}"
            )

            return {
                'file_id': file_id,
                'store_id': store_name,
                'metadata': {
                    'document_name': file_id,
                    'display_name': f"{resource.jurisdiction_abbrev} - {resource.display_name}",
                }
            }

        except Exception as exc:
            logger.error(
                "Failed to upload resource %s to Gemini: %s",
                resource.id,
                exc,
                exc_info=sys.exc_info()
            )
            # Note: Don't update status here - the signal handler manages status
            raise ProviderAPIError(f"Failed to upload resource: {exc}")

    def remove_resource(self, resource, file_id: str = None) -> None:
        """
        Remove a resource from File Search store.

        Args:
            resource: The JurisdictionResource being removed
            file_id: The provider-specific file ID to remove (from ResourceProviderUpload)
        """
        self._check_api_enabled()

        try:
            # Use provided file_id or fall back to legacy fields (for backward compatibility)
            file_to_delete = file_id or getattr(resource, 'provider_file_id', None) or resource.gemini_file_id

            if not file_to_delete:
                logger.warning(
                    f"Resource {resource.id} has no file_id, skipping removal"
                )
                return

            # Remove using the wrapped service
            # Note: The service expects the resource to have gemini_file_id set
            # so we temporarily set it if needed
            original_gemini_id = resource.gemini_file_id
            if not resource.gemini_file_id and file_to_delete:
                resource.gemini_file_id = file_to_delete

            self.service.remove_resource(resource)

            # Restore original value
            resource.gemini_file_id = original_gemini_id

            logger.info(f"Removed resource {resource.id} from Gemini File Search store")

        except Exception as exc:
            logger.error(
                "Failed to remove resource %s from Gemini: %s",
                resource.id,
                exc,
                exc_info=sys.exc_info()
            )
            # Don't raise - deletion should proceed

    def query(
        self,
        question: str,
        state: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query using Gemini File Search"""
        self._check_api_enabled()

        try:
            # Query using the wrapped service
            result = self.service.query(
                question=question,
                state=state,
                context=context,
                model=model or self.model,
                system_prompt=system_prompt
            )

            # Adapt response to match provider interface
            standardized_result = {
                'answer': result['answer'],
                'citations': result['citations'],
                'provider': self.PROVIDER_NAME,
                'model': model or self.model,
            }

            if state:
                standardized_result['state'] = state

            logger.info(
                f"Query completed: {len(result['answer'])} chars, "
                f"{len(result['citations'])} citations"
            )
            return standardized_result

        except Exception as exc:
            logger.error(
                "Failed to query Gemini: %s",
                exc,
                exc_info=sys.exc_info()
            )
            raise ProviderAPIError(f"Failed to query Gemini: {exc}")

    def query_stream(
        self,
        question: str,
        state: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Query with streaming response using Gemini File Search"""
        self._check_api_enabled()

        try:
            # Stream using the wrapped service
            for chunk in self.service.query_stream(
                question=question,
                state=state,
                context=context,
                model=model or self.model,
                system_prompt=system_prompt
            ):
                # Pass through chunks as-is (already in correct format)
                if chunk['type'] == 'chunk':
                    yield chunk
                elif chunk['type'] == 'citations':
                    yield chunk
                elif chunk['type'] == 'done':
                    # Add provider and model info to done chunk
                    yield {
                        'type': 'done',
                        'provider': self.PROVIDER_NAME,
                        'model': model or self.model
                    }
                elif chunk['type'] == 'error':
                    yield chunk

            logger.info("Streaming query completed")

        except Exception as exc:
            logger.error(
                "Failed to stream query from Gemini: %s",
                exc,
                exc_info=sys.exc_info()
            )
            yield {
                'type': 'error',
                'error': str(exc)
            }

    def get_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities"""
        info = super().get_info()

        # Add Gemini-specific information
        if self.service:
            info['request_stats'] = self.service.get_request_stats()

        return info
