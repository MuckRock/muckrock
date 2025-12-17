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

    # Override system instruction to request inline citations
    SYSTEM_INSTRUCTION = """
You are the State Public Records & FOIA Coach. Your role is to provide
accurate, well-cited guidance about state public records laws and best
practices for requesting public records.

CRITICAL RULES:
1. Base ALL responses strictly on the documents in your knowledge base
2. ALWAYS cite the source document inline for every piece of information using numbered citations like [1], [2], etc.
3. Place citation numbers immediately after the relevant statement or fact
4. If information is not in your knowledge base, explicitly say so
5. Do NOT generate request language - provide knowledge and coaching only
6. Focus on helping users understand the law and process
7. Highlight state-specific requirements, deadlines, and exemptions
8. Provide context about common pitfalls and best practices

CITATION FORMAT:
- Use inline numbered citations: "The request must be in writing [1]."
- Place citations after the relevant information
- Use the same number for repeated references to the same source
- Cite every factual claim

When answering questions:
- Quote relevant law sections with citations
- Explain deadlines and response times with citations
- Describe exemptions and their proper use with citations
- Suggest what information users should research further
- Encourage specificity in their requests
- Note any jurisdiction-specific procedures with citations

NEVER:
- Generate full request text
- Make legal claims beyond what's in documents
- Provide information from outside your knowledge base
- Make assumptions about unstated facts
- Make statements without proper inline citations
"""

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

                            logger.info("=" * 80)
                            logger.info("OPENAI RESPONSE DEBUG")
                            logger.info("=" * 80)
                            logger.info(f"Answer text (first 500 chars): {answer[:500]}")
                            logger.info(f"Answer text length: {len(answer)} characters")

                            # Extract citations from annotations
                            if hasattr(content, 'annotations') and content.annotations:
                                logger.info(f"\nFound {len(content.annotations)} annotations")

                                for idx, annotation in enumerate(content.annotations):
                                    logger.info(f"\n--- Annotation #{idx + 1} ---")
                                    logger.info(f"Type: {annotation.type}")
                                    logger.info(f"Available attributes: {dir(annotation)}")

                                    if annotation.type == "file_citation":
                                        citation = {
                                            'source': annotation.filename,
                                            'file_id': annotation.file_id,
                                        }

                                        logger.info(f"Filename: {annotation.filename}")
                                        logger.info(f"File ID: {annotation.file_id}")

                                        # Extract index information for inline citations
                                        if hasattr(annotation, 'text'):
                                            citation['text'] = annotation.text
                                            logger.info(f"Text: {annotation.text}")
                                        else:
                                            logger.info("Text: NOT PRESENT")

                                        if hasattr(annotation, 'start_index'):
                                            citation['start_index'] = annotation.start_index
                                            logger.info(f"Start index: {annotation.start_index}")
                                        else:
                                            logger.info("Start index: NOT PRESENT")

                                        if hasattr(annotation, 'end_index'):
                                            citation['end_index'] = annotation.end_index
                                            logger.info(f"End index: {annotation.end_index}")
                                        else:
                                            logger.info("End index: NOT PRESENT")

                                        if hasattr(annotation, 'index'):
                                            citation['index'] = annotation.index
                                            idx_pos = annotation.index
                                            logger.info(f"Index: {idx_pos}")
                                            # Show what's at that position in the text
                                            if 0 <= idx_pos < len(answer):
                                                context_start = max(0, idx_pos - 20)
                                                context_end = min(len(answer), idx_pos + 20)
                                                context = answer[context_start:context_end]
                                                logger.info(f"Text at index {idx_pos}: '...{context}...'")
                                                logger.info(f"Character at index: '{answer[idx_pos]}'")
                                        else:
                                            logger.info("Index: NOT PRESENT")

                                        # Extract quote if available
                                        if hasattr(annotation, 'quote'):
                                            citation['quote'] = annotation.quote
                                            logger.info(f"Quote: {annotation.quote[:100]}...")
                                        elif hasattr(annotation, 'file_citation') and hasattr(annotation.file_citation, 'quote'):
                                            citation['quote'] = annotation.file_citation.quote
                                            logger.info(f"Quote (from file_citation): {annotation.file_citation.quote[:100]}...")
                                        else:
                                            logger.info("Quote: NOT PRESENT")

                                        citations.append(citation)
                                        logger.info(f"Citation object: {citation}")
                            else:
                                logger.info("\nNo annotations found in response")

                            logger.info("=" * 80)

            # Insert inline citation markers into answer text
            if citations and answer:
                answer = self._insert_citation_markers(answer, citations)

            # Enrich citations with resource metadata
            citations = self._enrich_citations_with_resources(citations)

            logger.info("\n" + "=" * 80)
            logger.info("ENRICHED CITATIONS")
            logger.info("=" * 80)
            for idx, citation in enumerate(citations):
                logger.info(f"\nCitation #{idx + 1}:")
                logger.info(f"  Display Name: {citation.get('display_name')}")
                logger.info(f"  File URL: {citation.get('file_url')}")
                logger.info(f"  Jurisdiction: {citation.get('jurisdiction_abbrev')}")
                logger.info(f"  Has start_index: {citation.get('start_index') is not None}")
                logger.info(f"  Has end_index: {citation.get('end_index') is not None}")
                logger.info(f"  Full citation: {citation}")
            logger.info("=" * 80 + "\n")

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

    def _insert_citation_markers(self, answer: str, citations: list) -> str:
        """
        Insert numbered citation markers like [1], [2] into the answer text.

        OpenAI provides index positions but doesn't add the markers, so we do it ourselves.
        """
        if not citations or not answer:
            return answer

        # Filter citations that have index positions
        indexed_citations = [c for c in citations if c.get('index') is not None]
        if not indexed_citations:
            return answer

        # Sort citations by index in REVERSE order (to avoid index shifting when inserting)
        sorted_citations = sorted(indexed_citations, key=lambda c: c['index'], reverse=True)

        # Create mapping of file_id to citation number (for consistency)
        file_id_to_num = {}
        citation_num = 1
        # Process in forward order to assign numbers
        for citation in sorted(indexed_citations, key=lambda c: c['index']):
            file_id = citation.get('file_id')
            if file_id and file_id not in file_id_to_num:
                file_id_to_num[file_id] = citation_num
                citation_num += 1

        # Insert citation markers working backwards
        modified_answer = answer
        for citation in sorted_citations:
            idx = citation['index']
            file_id = citation.get('file_id')

            if file_id and file_id in file_id_to_num and 0 <= idx <= len(modified_answer):
                num = file_id_to_num[file_id]
                marker = f" [{num}]"

                # Insert marker after the index position
                modified_answer = modified_answer[:idx + 1] + marker + modified_answer[idx + 1:]

        logger.info(f"Inserted {len(file_id_to_num)} unique citation markers into answer")
        return modified_answer

    def _enrich_citations_with_resources(self, citations: list) -> list:
        """
        Enrich citations with JurisdictionResource metadata.

        Maps OpenAI file_ids to JurisdictionResource objects and adds:
        - display_name: Human-readable resource name
        - jurisdiction_abbrev: State abbreviation
        - file_url: URL to the uploaded PDF file
        """
        from django.conf import settings
        from apps.jurisdiction.models import ResourceProviderUpload

        if not citations:
            return citations

        # Get all file_ids from citations
        file_ids = [c.get('file_id') for c in citations if c.get('file_id')]

        if not file_ids:
            return citations

        # Look up ResourceProviderUpload objects by file_id
        uploads = ResourceProviderUpload.objects.filter(
            provider=self.PROVIDER_NAME,
            provider_file_id__in=file_ids
        ).select_related('resource')

        # Get the backend API URL for constructing absolute URLs
        backend_url = settings.BACKEND_API_URL.rstrip('/')

        # Create a mapping of file_id to resource data
        file_id_to_resource = {}
        for upload in uploads:
            resource = upload.resource
            # Build absolute URL for the file
            file_url = None
            if resource.file:
                relative_url = resource.file.url
                # If it's already an absolute URL, use it as is
                if relative_url.startswith('http://') or relative_url.startswith('https://'):
                    file_url = relative_url
                else:
                    # Construct absolute URL
                    file_url = f"{backend_url}{relative_url}"

            file_id_to_resource[upload.provider_file_id] = {
                'display_name': resource.display_name or resource.file.name,
                'jurisdiction_abbrev': resource.jurisdiction_abbrev,
                'file_url': file_url,
            }

        # Enrich each citation with resource metadata
        enriched_citations = []
        for citation in citations:
            file_id = citation.get('file_id')
            if file_id and file_id in file_id_to_resource:
                resource_data = file_id_to_resource[file_id]
                citation.update(resource_data)
            enriched_citations.append(citation)

        return enriched_citations

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
                                                citation = {
                                                    'source': annotation.filename,
                                                    'file_id': annotation.file_id,
                                                }

                                                # Extract index information for inline citations
                                                if hasattr(annotation, 'text'):
                                                    citation['text'] = annotation.text
                                                if hasattr(annotation, 'start_index'):
                                                    citation['start_index'] = annotation.start_index
                                                if hasattr(annotation, 'end_index'):
                                                    citation['end_index'] = annotation.end_index
                                                if hasattr(annotation, 'index'):
                                                    citation['index'] = annotation.index

                                                # Extract quote if available
                                                if hasattr(annotation, 'quote'):
                                                    citation['quote'] = annotation.quote
                                                elif hasattr(annotation, 'file_citation') and hasattr(annotation.file_citation, 'quote'):
                                                    citation['quote'] = annotation.file_citation.quote

                                                citations.append(citation)

                # Enrich citations with resource metadata
                citations = self._enrich_citations_with_resources(citations)

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
