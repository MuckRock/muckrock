"""
Mock provider implementation for testing.

This provider never makes real API calls and returns fake but realistic responses.
"""
from typing import Optional, Generator, Dict, Any
import logging
import uuid

from .base import RAGProviderBase, ProviderConfigError

logger = logging.getLogger(__name__)


class MockProvider(RAGProviderBase):
    """
    Mock provider for testing - never makes real API calls.

    Returns fake but realistic responses for all operations.
    Configurable behavior for testing different scenarios.
    """

    PROVIDER_NAME = 'mock'

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize mock provider"""
        super().__init__(config)

        # Mock configuration
        self.model = self.config.get('model', 'mock-model-1.0')
        self.store_name = self.config.get('store_name', 'MockStore')

        # Test behavior configuration
        self.should_fail = self.config.get('should_fail', False)
        self.fail_message = self.config.get('fail_message', 'Mock provider configured to fail')
        self.upload_delay = self.config.get('upload_delay', 0)  # Simulate delay (seconds)

        # Internal state for testing
        self._stores = {}  # Store ID -> name mapping
        self._files = {}  # File ID -> metadata mapping

        logger.info("MockProvider initialized (no real API calls will be made)")

    def create_store(self, display_name: str) -> str:
        """Create a mock store"""
        if self.should_fail:
            raise ProviderConfigError(self.fail_message)

        store_id = f"mock-store-{uuid.uuid4().hex[:8]}"
        self._stores[store_id] = display_name

        logger.info(f"Mock: Created store {store_id} with name '{display_name}'")
        return store_id

    def get_or_create_store(self, display_name: Optional[str] = None) -> str:
        """Get or create a mock store"""
        if self.should_fail:
            raise ProviderConfigError(self.fail_message)

        if display_name is None:
            display_name = self.store_name

        # Check if store with this name exists
        for store_id, name in self._stores.items():
            if name == display_name:
                logger.info(f"Mock: Found existing store {store_id}")
                return store_id

        # Create new store
        return self.create_store(display_name)

    def upload_resource(self, resource) -> Dict[str, Any]:
        """Upload a mock resource"""
        if self.should_fail:
            raise ProviderConfigError(self.fail_message)

        # Simulate upload delay if configured
        if self.upload_delay > 0:
            import time
            time.sleep(self.upload_delay)

        # Generate mock IDs
        file_id = f"mock-file-{uuid.uuid4().hex[:12]}"
        store_id = self.get_or_create_store()

        # Store file metadata
        self._files[file_id] = {
            'resource_id': resource.id,
            'display_name': resource.display_name,
            'jurisdiction': resource.jurisdiction_abbrev,
            'filename': resource.file.name,
            'store_id': store_id,
        }

        # Update resource status
        resource.index_status = 'ready'
        resource.indexed_at = None  # Would be set by real provider
        resource.save(update_fields=['index_status', 'indexed_at'])

        logger.info(f"Mock: Uploaded resource {resource.id} as {file_id}")

        return {
            'file_id': file_id,
            'store_id': store_id,
            'metadata': {
                'filename': resource.file.name,
                'display_name': resource.display_name,
                'mock': True,
            }
        }

    def remove_resource(self, resource) -> None:
        """Remove a mock resource"""
        if self.should_fail:
            raise ProviderConfigError(self.fail_message)

        file_id = resource.provider_file_id or resource.gemini_file_id

        if not file_id:
            logger.warning(f"Mock: Resource {resource.id} has no file_id, skipping")
            return

        # Remove from internal state
        if file_id in self._files:
            del self._files[file_id]
            logger.info(f"Mock: Removed resource {resource.id} file {file_id}")
        else:
            logger.warning(f"Mock: File {file_id} not found in mock state")

    def query(
        self,
        question: str,
        state: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return a mock query response"""
        if self.should_fail:
            raise ProviderConfigError(self.fail_message)

        # Generate a realistic mock response
        answer = self._generate_mock_answer(question, state)
        citations = self._generate_mock_citations(state)

        result = {
            'answer': answer,
            'citations': citations,
            'provider': self.PROVIDER_NAME,
            'model': model or self.model,
        }

        if state:
            result['state'] = state

        logger.info(
            f"Mock: Query completed - {len(answer)} chars, {len(citations)} citations"
        )
        return result

    def query_stream(
        self,
        question: str,
        state: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Return a mock streaming response"""
        if self.should_fail:
            yield {
                'type': 'error',
                'error': self.fail_message
            }
            return

        # Generate mock answer and stream it in chunks
        answer = self._generate_mock_answer(question, state)
        citations = self._generate_mock_citations(state)

        # Stream answer in chunks (simulate word-by-word streaming)
        words = answer.split()
        chunk_size = 5  # Words per chunk

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            if i + chunk_size < len(words):
                chunk_text += ' '

            yield {
                'type': 'chunk',
                'text': chunk_text
            }

        # Send citations
        yield {
            'type': 'citations',
            'citations': citations,
            'state': state
        }

        # Send done
        yield {
            'type': 'done',
            'provider': self.PROVIDER_NAME,
            'model': model or self.model
        }

        logger.info("Mock: Streaming query completed")

    def _generate_mock_answer(self, question: str, state: Optional[str] = None) -> str:
        """Generate a realistic mock answer"""
        state_text = f" for {state}" if state else ""

        # Generate different responses based on question content
        if 'deadline' in question.lower() or 'timeline' in question.lower():
            return (
                f"Mock response{state_text}: Public records requests typically have "
                "deadlines ranging from 3-10 business days, depending on the jurisdiction. "
                "Some states allow extensions for complex requests. This is a mock response "
                "for testing purposes and does not reflect actual legal requirements."
            )
        elif 'fee' in question.lower() or 'cost' in question.lower():
            return (
                f"Mock response{state_text}: Fees for public records requests vary by "
                "jurisdiction. Many states allow for search and copying fees, but may waive "
                "fees for small requests. This is a mock response for testing purposes."
            )
        elif 'exempt' in question.lower():
            return (
                f"Mock response{state_text}: Common exemptions to public records laws include "
                "privacy protections for personal information, law enforcement records, and "
                "attorney-client privileged documents. This is a mock response for testing."
            )
        else:
            return (
                f"Mock response{state_text}: This is a simulated answer to the question: "
                f'"{question[:50]}..." The mock provider does not make real API calls and '
                "returns this generic response for testing purposes. In production, a real "
                "provider would return accurate, cited information from your knowledge base."
            )

    def _generate_mock_citations(self, state: Optional[str] = None) -> list:
        """Generate realistic mock citations"""
        state_text = state or "State"

        return [
            {
                'source': f'{state_text} Public Records Act',
                'content': 'Mock citation content for testing purposes',
                'file_id': f'mock-file-{uuid.uuid4().hex[:8]}'
            },
            {
                'source': f'{state_text} FOIA Guidelines',
                'content': 'Additional mock citation for comprehensive testing',
                'file_id': f'mock-file-{uuid.uuid4().hex[:8]}'
            }
        ]

    def get_info(self) -> Dict[str, Any]:
        """Get mock provider information"""
        info = super().get_info()

        # Add mock-specific information
        info['mock_state'] = {
            'stores': len(self._stores),
            'files': len(self._files),
            'should_fail': self.should_fail,
        }

        return info

    def reset(self):
        """Reset mock provider state (useful for tests)"""
        self._stores = {}
        self._files = {}
        logger.info("Mock: Provider state reset")

    def configure_failure(self, should_fail: bool = True, message: str = None):
        """Configure mock provider to fail (useful for error testing)"""
        self.should_fail = should_fail
        if message:
            self.fail_message = message
        logger.info(f"Mock: Configured failure mode - should_fail={should_fail}")
