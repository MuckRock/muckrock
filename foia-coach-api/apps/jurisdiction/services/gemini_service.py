"""
Gemini File Search Service

Service for managing Google Gemini File Search integration for FOIA Coach.
Handles file uploads, indexing, and RAG-powered queries for state public records guidance.
"""

# Django
from django.conf import settings
from django.utils import timezone

# Standard Library
import logging
import mimetypes
import sys
from datetime import datetime
from typing import Generator, Optional

# Third Party
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiFileSearchService:
    """Service for managing Gemini File Search integration"""

    # Class-level request tracking (shared across all instances in this process)
    _request_count = 0
    _request_history = []  # List of timestamps for rate limiting
    _max_requests_per_session = 200  # Alert threshold for development
    _max_requests_per_minute = 50  # Conservative limit (Gemini free tier: 60 QPM)

    # System instruction for the FOIA Coach expert persona
    SYSTEM_INSTRUCTION = """
You are the State Public Records & FOIA Coach. Your role is to provide
accurate, well-cited guidance about state public records laws and best
practices for requesting public records.

CRITICAL RULES:
1. Base ALL responses strictly on the documents in your knowledge base
2. ALWAYS cite the source document for every piece of information
3. If information is not in your knowledge base, explicitly say so
4. Do NOT generate request language - provide knowledge and coaching only
5. Focus on helping users understand the law and process
6. Highlight state-specific requirements, deadlines, and exemptions
7. Provide context about common pitfalls and best practices

When answering questions:
- Quote relevant law sections with citations
- Explain deadlines and response times
- Describe exemptions and their proper use
- Suggest what information users should research further
- Encourage specificity in their requests
- Note any jurisdiction-specific procedures

NEVER:
- Generate full request text
- Make legal claims beyond what's in documents
- Provide information from outside your knowledge base
- Make assumptions about unstated facts
"""

    def __init__(self):
        """Initialize the Gemini client"""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not configured")

        # Check if real API calls are enabled
        self.real_api_enabled = getattr(settings, 'GEMINI_REAL_API_ENABLED', False)

        if not self.real_api_enabled:
            logger.warning(
                "⚠️  GEMINI_REAL_API_ENABLED is False - Real API calls are DISABLED. "
                "Set GEMINI_REAL_API_ENABLED=true in environment to enable."
            )

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if self.real_api_enabled else None
        self.store_name = settings.GEMINI_FILE_SEARCH_STORE_NAME

        # Initialize mimetypes and add common file type mappings
        if not mimetypes.inited:
            mimetypes.init()

        # Add markdown file types
        mimetypes.add_type('text/markdown', '.md')
        mimetypes.add_type('text/markdown', '.markdown')

        # Add Microsoft Office formats
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx')
        mimetypes.add_type('application/msword', '.doc')
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')
        mimetypes.add_type('application/vnd.ms-excel', '.xls')
        mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')
        mimetypes.add_type('application/vnd.ms-powerpoint', '.ppt')

    @classmethod
    def _track_request(cls):
        """Track an API request and check rate limits"""
        import time

        current_time = time.time()
        cls._request_count += 1
        cls._request_history.append(current_time)

        # Clean up old request history (older than 1 minute)
        one_minute_ago = current_time - 60
        cls._request_history = [t for t in cls._request_history if t > one_minute_ago]

        # Check session limit
        if cls._request_count > cls._max_requests_per_session:
            logger.error(
                f"⚠️  GEMINI API USAGE WARNING: {cls._request_count} requests made this session! "
                f"This is likely a bug (infinite loop or missing mocks in tests)."
            )
        elif cls._request_count % 50 == 0:
            logger.warning(
                f"Gemini API: {cls._request_count} requests made this session. "
                f"{len(cls._request_history)} requests in the last minute."
            )

        # Check rate limit (requests per minute)
        if len(cls._request_history) > cls._max_requests_per_minute:
            logger.error(
                f"⚠️  RATE LIMIT WARNING: {len(cls._request_history)} requests in the last minute! "
                f"Gemini free tier limit is 60 QPM. You may get 429 errors."
            )

    @classmethod
    def get_request_stats(cls) -> dict:
        """Get current request statistics for debugging"""
        import time
        one_minute_ago = time.time() - 60
        recent_requests = [t for t in cls._request_history if t > one_minute_ago]

        return {
            'total_requests_this_session': cls._request_count,
            'requests_last_minute': len(recent_requests),
            'rate_limit_threshold': cls._max_requests_per_minute,
            'session_limit_threshold': cls._max_requests_per_session,
        }

    @classmethod
    def reset_request_tracking(cls):
        """Reset request tracking (useful for tests)"""
        cls._request_count = 0
        cls._request_history = []

    def _check_api_enabled(self):
        """Check if real API calls are enabled, raise error if not"""
        if not self.real_api_enabled:
            raise RuntimeError(
                "Gemini API calls are disabled. "
                "Set GEMINI_REAL_API_ENABLED=true in environment to enable real API calls. "
                "This safety check prevents accidental API usage during development."
            )

    def create_store(self, display_name: Optional[str] = None) -> str:
        """
        Create a new File Search store.
        Returns the name of the created store.
        """
        # Check if API calls are enabled
        self._check_api_enabled()

        if display_name is None:
            display_name = self.store_name

        try:
            # Track API request
            self._track_request()

            # Create a new File Search store
            store = self.client.file_search_stores.create(
                config={'display_name': display_name}
            )
            logger.info(f"Created File Search store: {store.name}")
            return store.name

        except Exception as exc:
            logger.error(
                "Failed to create File Search store: %s",
                exc,
                exc_info=sys.exc_info(),
            )
            raise

    def get_or_create_store(self) -> str:
        """
        Get existing store or create if it doesn't exist.
        Returns the store name.
        """
        # Check if API calls are enabled
        self._check_api_enabled()

        try:
            # Track API request
            self._track_request()

            # List existing file search stores to check if our store exists
            stores = list(self.client.file_search_stores.list())
            for store in stores:
                if store.display_name == self.store_name:
                    logger.info(f"Found existing File Search store: {store.name}")
                    return store.name

            # Store doesn't exist, create it
            return self.create_store()

        except Exception as exc:
            logger.error(
                "Failed to get or create store: %s",
                exc,
                exc_info=sys.exc_info(),
            )
            raise

    def upload_resource(self, resource) -> str:
        """
        Upload a resource file directly to File Search store.
        """
        # Check if API calls are enabled
        self._check_api_enabled()

        try:
            # Get or create the File Search store
            store_name = self.get_or_create_store()

            # Prepare display name
            display_name = f"{resource.jurisdiction_abbrev} - {resource.display_name}"

            # Detect MIME type from file extension
            file_name = resource.file.name
            mime_type, _ = mimetypes.guess_type(file_name)

            # Default to text/plain if MIME type cannot be determined
            if not mime_type:
                logger.warning(
                    f"Could not determine MIME type for {file_name}, defaulting to text/plain"
                )
                mime_type = 'text/plain'

            logger.info(f"Detected MIME type for {file_name}: {mime_type}")

            # Extract file extension for temp file (if needed)
            import os
            file_ext = os.path.splitext(file_name)[1] or '.txt'

            # Update status to uploading
            resource.index_status = 'uploading'
            resource.save(update_fields=['index_status'])

            # Track API request for upload
            self._track_request()

            # Upload file directly to File Search store
            # Try to use path if available, otherwise create temp file
            try:
                # For file storage backends that support .path
                operation = self.client.file_search_stores.upload_to_file_search_store(
                    file=resource.file.path,
                    file_search_store_name=store_name,
                    config={'display_name': display_name, 'mime_type': mime_type}
                )
            except (AttributeError, NotImplementedError):
                # For storage backends that don't support .path (e.g., S3, InMemoryStorage)
                # Write to a temporary file first
                import tempfile

                resource.file.seek(0)
                file_content = resource.file.read()

                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                    tmp_file.write(file_content if isinstance(file_content, bytes) else file_content.encode())
                    tmp_file.flush()
                    temp_path = tmp_file.name

                try:
                    operation = self.client.file_search_stores.upload_to_file_search_store(
                        file=temp_path,
                        file_search_store_name=store_name,
                        config={'display_name': display_name, 'mime_type': mime_type}
                    )
                finally:
                    # Clean up temp file
                    os.unlink(temp_path)

            # Check if operation is already complete or needs polling
            # In newer API versions, the operation completes immediately
            if hasattr(operation.done, '__call__'):
                # done is a method - need to poll
                import time
                while not operation.done():
                    time.sleep(1)
                    self._track_request()  # Track each polling request
                    operation = self.client.operations.get(name=operation.name)
                file_ref = operation.response
            else:
                # done is an attribute (None means complete) - use response directly
                file_ref = operation.response

            # Extract the document name/ID from the response
            # Response has document_name attribute
            file_id = file_ref.document_name if hasattr(file_ref, 'document_name') else file_ref.name
            resource.gemini_file_id = file_id
            resource.index_status = 'ready'
            resource.indexed_at = timezone.now()
            resource.save(update_fields=['gemini_file_id', 'index_status', 'indexed_at'])

            logger.info(
                f"Uploaded resource {resource.id} to File Search store: {file_id}"
            )
            return file_id

        except Exception as exc:
            logger.error(
                "Failed to upload resource %s: %s",
                resource.id,
                exc,
                exc_info=sys.exc_info(),
            )
            resource.index_status = 'error'
            resource.save(update_fields=['index_status'])
            raise

    def remove_resource(self, resource) -> None:
        """
        Remove a resource from File Search store (for delete signal)
        """
        # Check if API calls are enabled
        self._check_api_enabled()

        try:
            if not resource.gemini_file_id:
                logger.warning(
                    f"Resource {resource.id} has no gemini_file_id, skipping removal"
                )
                return

            # Get the File Search store
            store_name = self.get_or_create_store()

            # Track API request for deletion
            self._track_request()

            # Delete the file from File Search store
            self.client.file_search_stores.delete_file(
                file_search_store_name=store_name,
                file_name=resource.gemini_file_id
            )

            logger.info(
                f"Removed resource {resource.id} from File Search store: "
                f"{resource.gemini_file_id}"
            )

        except Exception as exc:
            logger.error(
                "Failed to remove resource %s: %s",
                resource.id,
                exc,
                exc_info=sys.exc_info(),
            )
            # Don't raise - deletion should still proceed in Django

    def query(
        self,
        question: str,
        state: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None
    ) -> dict:
        """
        Query the RAG system with a question

        Args:
            question: The user's question
            state: Optional state filter (e.g., 'CO', 'GA', 'TN')
            context: Optional additional context
            model: Optional Gemini model to use (defaults to settings.GEMINI_MODEL)

        Returns:
            Dict with 'answer', 'citations', and optional 'state'
        """
        # Check if API calls are enabled
        self._check_api_enabled()

        try:
            # Get the File Search store
            store_name = self.get_or_create_store()

            # Use provided model or fall back to settings
            model_name = model or settings.GEMINI_MODEL

            # Build the prompt with optional state filter
            prompt = question
            if state:
                prompt = f"[Context: {state}] {question}"

            # Track API request for query
            self._track_request()

            # Generate content with File Search grounding
            # Note: Using dict-based config because types.FileSearch not available in v1.2.0
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "system_instruction": self.SYSTEM_INSTRUCTION,
                    "tools": [{
                        "file_search": {
                            "file_search_store_names": [store_name]
                        }
                    }]
                }
            )

            # Extract answer and citations
            answer = response.text
            citations = self._extract_citations(response)

            result = {
                'answer': answer,
                'citations': citations,
            }

            if state:
                result['state'] = state

            logger.info(f"Query completed: {len(answer)} chars, {len(citations)} citations")
            return result

        except Exception as exc:
            logger.error(
                "Failed to query Gemini: %s",
                exc,
                exc_info=sys.exc_info(),
            )
            raise

    def query_stream(
        self,
        question: str,
        state: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None
    ) -> Generator[dict, None, None]:
        """
        Query the RAG system with streaming response

        Args:
            question: The user's question
            state: Optional state filter (e.g., 'CO', 'GA', 'TN')
            context: Optional additional context
            model: Optional Gemini model to use (defaults to settings.GEMINI_MODEL)

        Yields:
            Dicts with incremental response data:
            - {'type': 'chunk', 'text': '...'} for text chunks
            - {'type': 'citations', 'citations': [...]} for final citations
            - {'type': 'done'} when complete
        """
        # Check if API calls are enabled
        self._check_api_enabled()

        try:
            # Get the File Search store
            store_name = self.get_or_create_store()

            # Use provided model or fall back to settings
            model_name = model or settings.GEMINI_MODEL

            # Build the prompt with optional state filter
            prompt = question
            if state:
                prompt = f"[Context: {state}] {question}"

            # Track API request for streaming query
            self._track_request()

            # Generate content with File Search streaming
            # Note: Using dict-based config because types.FileSearch not available in v1.2.0
            response_stream = self.client.models.generate_content_stream(
                model=model_name,
                contents=prompt,
                config={
                    "system_instruction": self.SYSTEM_INSTRUCTION,
                    "tools": [{
                        "file_search": {
                            "file_search_store_names": [store_name]
                        }
                    }]
                }
            )

            # Stream the response chunks
            full_response = None
            for chunk in response_stream:
                if chunk.text:
                    yield {
                        'type': 'chunk',
                        'text': chunk.text
                    }
                full_response = chunk

            # Send citations at the end
            if full_response:
                citations = self._extract_citations(full_response)
                yield {
                    'type': 'citations',
                    'citations': citations,
                    'state': state
                }

            yield {'type': 'done'}

            logger.info("Streaming query completed")

        except Exception as exc:
            logger.error(
                "Failed to stream query: %s",
                exc,
                exc_info=sys.exc_info(),
            )
            yield {
                'type': 'error',
                'error': str(exc)
            }

    def _extract_citations(self, response) -> list:
        """
        Extract citations from Gemini response
        """
        citations = []

        # Check if response has grounding metadata
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata'):
                metadata = candidate.grounding_metadata
                if hasattr(metadata, 'grounding_chunks'):
                    for chunk in metadata.grounding_chunks:
                        if hasattr(chunk, 'web'):
                            citations.append({
                                'source': chunk.web.uri,
                                'display_name': chunk.web.title or chunk.web.uri
                            })

        return citations
