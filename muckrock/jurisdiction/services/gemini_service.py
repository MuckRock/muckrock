"""
Gemini File Search Service

Service for managing Google Gemini File Search integration for FOIA Coach.
Handles file uploads, indexing, and RAG-powered queries for state public records guidance.
"""

# Django
from django.conf import settings

# Standard Library
import logging
import sys
from datetime import datetime
from typing import Generator, Optional

# Third Party
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiFileSearchService:
    """Service for managing Gemini File Search integration"""

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
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.store_name = settings.GEMINI_FILE_SEARCH_STORE_NAME

    def create_store(self, display_name: Optional[str] = None) -> str:
        """
        Create a new File Search store.
        Returns the name of the created store.
        """
        if display_name is None:
            display_name = self.store_name

        try:
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
        try:
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
        try:
            # Get or create the File Search store
            store_name = self.get_or_create_store()

            # Prepare display name
            display_name = f"{resource.jurisdiction.abbrev} - {resource.display_name}"

            # Update status to uploading
            resource.index_status = 'uploading'
            resource.save(update_fields=['index_status'])

            # Upload file directly to File Search store
            # Try to use path if available, otherwise create temp file
            try:
                # For file storage backends that support .path
                operation = self.client.file_search_stores.upload_to_file_search_store(
                    file=resource.file.path,
                    file_search_store_name=store_name,
                    config={'display_name': display_name}
                )
            except (AttributeError, NotImplementedError):
                # For storage backends that don't support .path (e.g., S3, InMemoryStorage)
                # Write to a temporary file first
                import tempfile
                import os

                resource.file.seek(0)
                file_content = resource.file.read()

                with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp_file:
                    tmp_file.write(file_content if isinstance(file_content, bytes) else file_content.encode())
                    tmp_file.flush()
                    temp_path = tmp_file.name

                try:
                    operation = self.client.file_search_stores.upload_to_file_search_store(
                        file=temp_path,
                        file_search_store_name=store_name,
                        config={'display_name': display_name}
                    )
                finally:
                    # Clean up temp file
                    os.unlink(temp_path)

            # Wait for operation to complete
            import time
            while not operation.done():
                time.sleep(1)
                operation = self.client.operations.get(name=operation.name)

            # Get the file reference from the completed operation
            file_ref = operation.response

            resource.gemini_file_id = file_ref.name
            resource.index_status = 'ready'
            resource.indexed_at = datetime.now()
            resource.save(update_fields=['gemini_file_id', 'index_status', 'indexed_at'])

            logger.info(
                f"Uploaded resource {resource.id} to File Search store: {file_ref.name}"
            )
            return file_ref.name

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
        try:
            if not resource.gemini_file_id:
                logger.warning(
                    f"Resource {resource.id} has no gemini_file_id, skipping removal"
                )
                return

            # Get the File Search store
            store_name = self.get_or_create_store()

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
        context: Optional[dict] = None
    ) -> dict:
        """
        Query the RAG system with a question

        Args:
            question: The user's question
            state: Optional state filter (e.g., 'CO', 'GA', 'TN')
            context: Optional additional context

        Returns:
            Dict with 'answer', 'citations', and optional 'state'
        """
        try:
            # Get the File Search store
            store_name = self.get_or_create_store()

            # Build the prompt with optional state filter
            prompt = question
            if state:
                prompt = f"[Context: {state}] {question}"

            # Generate content with File Search grounding
            # Note: Using dict-based config because types.FileSearch not available in v1.2.0
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
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
        context: Optional[dict] = None
    ) -> Generator[dict, None, None]:
        """
        Query the RAG system with streaming response

        Args:
            question: The user's question
            state: Optional state filter (e.g., 'CO', 'GA', 'TN')
            context: Optional additional context

        Yields:
            Dicts with incremental response data:
            - {'type': 'chunk', 'text': '...'} for text chunks
            - {'type': 'citations', 'citations': [...]} for final citations
            - {'type': 'done'} when complete
        """
        try:
            # Get the File Search store
            store_name = self.get_or_create_store()

            # Build the prompt with optional state filter
            prompt = question
            if state:
                prompt = f"[Context: {state}] {question}"

            # Generate content with File Search streaming
            # Note: Using dict-based config because types.FileSearch not available in v1.2.0
            response_stream = self.client.models.generate_content_stream(
                model='gemini-2.0-flash-exp',
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
