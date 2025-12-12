"""
OpenAI provider implementation using Vector Stores and Responses API.
"""
from django.utils import timezone
from typing import Optional, Generator, Dict, Any
import logging
import sys
import os

from openai import OpenAI

from .base import RAGProviderBase, ProviderError, ProviderConfigError, ProviderAPIError

logger = logging.getLogger(__name__)


class OpenAIProvider(RAGProviderBase):
    """
    OpenAI provider implementation using Vector Stores and Responses API.

    Uses the simpler Responses API instead of Assistants API - no threads needed!
    """

    PROVIDER_NAME = 'openai'

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI provider"""
        super().__init__(config)

        # Get configuration
        self.api_key = self.config.get('api_key')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not configured")

        self.model = self.config.get('model', 'gpt-4.1')
        self.vector_store_name = self.config.get(
            'vector_store_name', 'StatePublicRecordsStore'
        )
        self.real_api_enabled = self.config.get('real_api_enabled', False)

        if not self.real_api_enabled:
            logger.warning(
                "⚠️  OPENAI_REAL_API_ENABLED is False - Real API calls are DISABLED. "
                "Set OPENAI_REAL_API_ENABLED=true in environment to enable."
            )

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key) if self.real_api_enabled else None

    def _check_api_enabled(self):
        """Check if real API calls are enabled"""
        if not self.real_api_enabled:
            raise ProviderConfigError(
                "OpenAI API calls are disabled. "
                "Set OPENAI_REAL_API_ENABLED=true in environment to enable."
            )

    def create_store(self, display_name: str) -> str:
        """Create a new vector store"""
        self._check_api_enabled()

        try:
            vector_store = self.client.vector_stores.create(
                name=display_name
            )
            logger.info(f"Created vector store: {vector_store.id}")
            return vector_store.id

        except Exception as exc:
            logger.error(
                "Failed to create vector store: %s",
                exc,
                exc_info=sys.exc_info()
            )
            raise ProviderAPIError(f"Failed to create vector store: {exc}")

    def get_or_create_store(self, display_name: Optional[str] = None) -> str:
        """Get existing vector store or create new one"""
        self._check_api_enabled()

        if display_name is None:
            display_name = self.vector_store_name

        try:
            # List existing vector stores
            vector_stores = self.client.vector_stores.list()
            for store in vector_stores.data:
                if store.name == display_name:
                    logger.info(f"Found existing vector store: {store.id}")
                    return store.id

            # Store doesn't exist, create it
            return self.create_store(display_name)

        except Exception as exc:
            logger.error(
                "Failed to get or create vector store: %s",
                exc,
                exc_info=sys.exc_info()
            )
            raise ProviderAPIError(f"Failed to get or create vector store: {exc}")

    def upload_resource(self, resource) -> Dict[str, Any]:
        """Upload a resource file to vector store"""
        self._check_api_enabled()

        try:
            # Get or create vector store
            store_id = self.get_or_create_store()

            # Note: Status is managed by the signal handler, not here

            # Upload file to OpenAI
            # Try to use path if available
            try:
                with open(resource.file.path, 'rb') as file_stream:
                    file_obj = self.client.files.create(
                        file=file_stream,
                        purpose='assistants'
                    )
            except (AttributeError, NotImplementedError):
                # For storage backends without .path (S3, etc.)
                import tempfile

                resource.file.seek(0)
                file_content = resource.file.read()

                file_ext = os.path.splitext(resource.file.name)[1] or '.txt'
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=file_ext
                ) as tmp_file:
                    tmp_file.write(
                        file_content if isinstance(file_content, bytes)
                        else file_content.encode()
                    )
                    tmp_file.flush()
                    temp_path = tmp_file.name

                try:
                    with open(temp_path, 'rb') as file_stream:
                        file_obj = self.client.files.create(
                            file=file_stream,
                            purpose='assistants'
                        )
                finally:
                    os.unlink(temp_path)

            # Add file to vector store
            self.client.vector_stores.files.create(
                vector_store_id=store_id,
                file_id=file_obj.id
            )

            # Wait for file to be processed (poll status)
            import time
            max_wait = 60  # seconds
            elapsed = 0
            while elapsed < max_wait:
                vector_store_file = self.client.vector_stores.files.retrieve(
                    vector_store_id=store_id,
                    file_id=file_obj.id
                )
                if vector_store_file.status == 'completed':
                    break
                elif vector_store_file.status == 'failed':
                    raise ProviderAPIError(
                        f"File processing failed: {vector_store_file.last_error}"
                    )
                time.sleep(2)
                elapsed += 2

            # Check if we timed out
            if elapsed >= max_wait and vector_store_file.status != 'completed':
                logger.warning(
                    f"File {file_obj.id} processing timeout after {max_wait}s "
                    f"(status: {vector_store_file.status}). Continuing anyway."
                )

            logger.info(
                f"Uploaded resource {resource.id} to vector store: {file_obj.id} "
                f"(status: {vector_store_file.status})"
            )

            return {
                'file_id': file_obj.id,
                'store_id': store_id,
                'metadata': {
                    'filename': file_obj.filename,
                    'bytes': file_obj.bytes,
                    'status': vector_store_file.status,
                }
            }

        except Exception as exc:
            logger.error(
                "Failed to upload resource %s: %s",
                resource.id,
                exc,
                exc_info=sys.exc_info()
            )
            # Note: Don't update status here - the signal handler manages status
            raise ProviderAPIError(f"Failed to upload resource: {exc}")

    def remove_resource(self, resource, file_id: str = None) -> None:
        """
        Remove a resource from vector store.

        Args:
            resource: The JurisdictionResource being removed
            file_id: The provider-specific file ID to remove (from ResourceProviderUpload)
        """
        self._check_api_enabled()

        try:
            # Use provided file_id or fall back to legacy field (for backward compatibility)
            file_to_delete = file_id or getattr(resource, 'provider_file_id', None)

            if not file_to_delete:
                logger.warning(
                    f"Resource {resource.id} has no file_id to delete, skipping"
                )
                return

            # Delete file from OpenAI
            self.client.files.delete(file_to_delete)
            logger.info(f"Removed resource {resource.id} file: {file_to_delete}")

        except Exception as exc:
            logger.error(
                "Failed to remove resource %s: %s",
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
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query using Responses API with file search"""
        self._check_api_enabled()

        try:
            # Get vector store
            store_id = self.get_or_create_store()

            # Build input with state filter and system instruction
            input_text = question
            if state:
                input_text = f"[Context: {state}] {question}"

            # Use Responses API with file_search tool
            response = self.client.responses.create(
                model=model or self.model,
                input=f"{self.SYSTEM_INSTRUCTION}\n\n{input_text}",
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [store_id]
                }],
                include=["file_search_call.results"]  # Include search results for citations
            )

            # Extract answer and citations from response
            answer = ""
            citations = []

            # Process output items
            for item in response.output:
                if item.type == "message" and item.role == "assistant":
                    # Extract message content
                    for content in item.content:
                        if content.type == "output_text":
                            answer = content.text

                            # Extract citations from annotations
                            if hasattr(content, 'annotations') and content.annotations:
                                for annotation in content.annotations:
                                    if annotation.type == "file_citation":
                                        citations.append({
                                            'source': annotation.filename,
                                            'file_id': annotation.file_id,
                                            'content': ""  # Quote not available in basic annotations
                                        })

            result = {
                'answer': answer,
                'citations': citations,
                'provider': self.PROVIDER_NAME,
                'model': model or self.model,
            }

            if state:
                result['state'] = state

            logger.info(
                f"Query completed: {len(answer)} chars, {len(citations)} citations"
            )
            return result

        except Exception as exc:
            logger.error(
                "Failed to query OpenAI: %s",
                exc,
                exc_info=sys.exc_info()
            )
            raise ProviderAPIError(f"Failed to query OpenAI: {exc}")

    def query_stream(
        self,
        question: str,
        state: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Query with streaming response using Responses API.

        Note: Streaming support for Responses API needs verification from OpenAI docs.
        If streaming is not supported, this falls back to non-streaming query.
        """
        self._check_api_enabled()

        try:
            # Get vector store
            store_id = self.get_or_create_store()

            # Build input with state filter and system instruction
            input_text = question
            if state:
                input_text = f"[Context: {state}] {question}"

            # Attempt to use streaming if supported
            # Note: Verify if client.responses.create supports stream=True parameter
            try:
                stream = self.client.responses.create(
                    model=model or self.model,
                    input=f"{self.SYSTEM_INSTRUCTION}\n\n{input_text}",
                    tools=[{
                        "type": "file_search",
                        "vector_store_ids": [store_id]
                    }],
                    include=["file_search_call.results"],
                    stream=True  # May need verification
                )

                citations = []
                for chunk in stream:
                    # Stream text chunks
                    if hasattr(chunk, 'output'):
                        for item in chunk.output:
                            if item.type == "message" and item.role == "assistant":
                                for content in item.content:
                                    if content.type == "output_text" and content.text:
                                        yield {
                                            'type': 'chunk',
                                            'text': content.text
                                        }

                                    # Collect citations
                                    if hasattr(content, 'annotations') and content.annotations:
                                        for annotation in content.annotations:
                                            if annotation.type == "file_citation":
                                                citations.append({
                                                    'source': annotation.filename,
                                                    'file_id': annotation.file_id,
                                                    'content': ""
                                                })

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

            except (TypeError, AttributeError) as stream_error:
                # Streaming not supported, fall back to non-streaming
                logger.warning(
                    f"Streaming not supported, using non-streaming query: {stream_error}"
                )
                result = self.query(question, state, context, model)

                # Yield full response as single chunk
                yield {
                    'type': 'chunk',
                    'text': result['answer']
                }
                yield {
                    'type': 'citations',
                    'citations': result['citations'],
                    'state': state
                }
                yield {
                    'type': 'done',
                    'provider': self.PROVIDER_NAME,
                    'model': model or self.model
                }

            logger.info("Streaming query completed")

        except Exception as exc:
            logger.error(
                "Failed to stream query: %s",
                exc,
                exc_info=sys.exc_info()
            )
            yield {
                'type': 'error',
                'error': str(exc)
            }
