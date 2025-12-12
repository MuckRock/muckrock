# FOIA Coach Multi-Provider Support - Implementation Plan

## Progress Tracker

**Last Updated:** 2025-12-12

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| Phase 1: Abstract Provider Interface | ✅ Complete | 2025-12-12 | Base class, factory, and exceptions created (commit: 1b57f0033) |
| Phase 2: OpenAI Provider Implementation | 🔲 Not Started | - | OpenAI File Search + Assistants API |
| Phase 3: Refactor Gemini to Provider Pattern | 🔲 Not Started | - | Adapt existing Gemini service to new interface |
| Phase 4: Provider Configuration & Selection | 🔲 Not Started | - | Settings and runtime provider switching |
| Phase 5: Update Models & Signals | 🔲 Not Started | - | Provider-agnostic metadata fields |
| Phase 6: Test Infrastructure & Mocking | 🔲 Not Started | - | Ensure no live API calls in tests |
| Phase 7: Management Commands & API Updates | 🔲 Not Started | - | Provider-aware commands and endpoints |
| Phase 8: Documentation & Testing | 🔲 Not Started | - | Complete docs and end-to-end validation |

---

## Executive Summary

Refactor the FOIA Coach API to support multiple LLM service providers (OpenAI, Gemini, and future providers) with a consistent internal API. This enables switching between providers for testing, comparison, and redundancy while maintaining a clean architecture.

## Problem Statement

**Current Issues:**
- Tightly coupled to Gemini API (File Search specific)
- Gemini API quota limits causing development issues
- Unable to compare quality/cost across different LLM providers
- Single point of failure if Gemini has issues

**Solution:**
- Abstract provider interface for RAG operations
- OpenAI implementation using Vector Stores + Assistants API
- Gemini implementation adapted to match interface
- Configuration-based provider selection
- Mock providers for testing (no live API calls in tests)

---

## Architecture Overview

### Provider Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FOIA Coach API                           │
│  (Models, Signals, Management Commands, REST API)           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Uses
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              RAGProviderFactory                             │
│  - Creates provider instances based on configuration        │
│  - get_provider() -> RAGProviderBase                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Returns
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              RAGProviderBase (Abstract)                     │
│  - create_store() -> str                                    │
│  - upload_resource(resource) -> str                         │
│  - remove_resource(resource) -> None                        │
│  - query(question, state, context) -> dict                  │
│  - query_stream(question, state, context) -> Generator      │
└───────────────────────┬─────────────────────────────────────┘
                        │
           ┌────────────┴────────────┬─────────────────┐
           │                         │                  │
           ▼                         ▼                  ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐
│  GeminiProvider      │  │  OpenAIProvider  │  │  MockProvider│
│  - google-genai      │  │  - openai        │  │  - (testing) │
│  - File Search API   │  │  - Vector Stores │  │  - No API    │
└──────────────────────┘  └──────────────────┘  └──────────────┘
```

### Provider Metadata Strategy

**Model Fields (Provider-Agnostic):**
- `provider` - String field: 'openai', 'gemini', 'mock'
- `provider_file_id` - Generic file/document ID from provider
- `provider_store_id` - Generic store/vector store ID from provider
- `provider_metadata` - JSONField for provider-specific data

**Backward Compatibility:**
- Keep existing `gemini_file_id` field for migration period
- Copy to `provider_file_id` when provider='gemini'
- Eventually deprecate and remove `gemini_*` fields

---

## OpenAI vs Gemini API Comparison

| Feature | Gemini File Search | OpenAI File Search (Responses API) |
|---------|-------------------|-------------------|
| **Storage** | File Search Store | Vector Store |
| **File Upload** | Direct to store | Upload file, then add to vector store |
| **Querying** | generate_content() with tools | responses.create() with file_search tool |
| **Streaming** | generate_content_stream() | responses.create(stream=True) |
| **Context** | Inline in prompt | Inline in input parameter |
| **Citations** | grounding_metadata | annotations in message content |
| **Rate Limits (Free tier)** | 60 RPM, 2M TPM | 100 RPM (Tier 1) |
| **File Size Limit** | 10 MB | 512 MB per file |
| **Supported Formats** | Text, PDF, DOCX, etc. | Text, PDF, DOCX, XLSX, PPTX, code files |
| **API Complexity** | Medium | Simple (no assistants/threads) |

---

## Implementation Phases

Each phase is designed to:
- **Complete in 45-90 minutes** (manageable chunks)
- Fit within single Claude Code session
- Result in a working, committable state
- Be independently testable
- Build incrementally on previous phases

**Critical Testing Requirement:**
- NO live API calls in any automated tests
- All tests must use mocks or the MockProvider
- Safety checks enforced via environment variables

---

### Phase 1: Abstract Provider Interface (45-60 minutes)

**Goal:** Define the abstract base class and provider contract that all implementations must follow.

**Note:** Pure interface definition - no implementation yet. Sets the foundation for all future work.

#### Tasks

1. **Create provider base class** (apps/jurisdiction/services/providers/base.py)
   ```python
   """
   Abstract base class for RAG providers.
   """
   from abc import ABC, abstractmethod
   from typing import Optional, Generator, Dict, Any


   class RAGProviderBase(ABC):
       """
       Abstract base class for all RAG provider implementations.

       All providers must implement file storage, indexing, and
       retrieval-augmented generation (RAG) queries.
       """

       # Provider identifier (e.g., 'openai', 'gemini', 'mock')
       PROVIDER_NAME: str = None

       # System instruction for FOIA Coach persona
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

       def __init__(self, config: Optional[Dict[str, Any]] = None):
           """
           Initialize the provider with optional configuration.

           Args:
               config: Provider-specific configuration dict
           """
           self.config = config or {}

       @abstractmethod
       def create_store(self, display_name: str) -> str:
           """
           Create a new knowledge store (vector store, file search store, etc.).

           Args:
               display_name: Human-readable name for the store

           Returns:
               Store ID/name that can be used in future operations

           Raises:
               ProviderError: If store creation fails
           """
           pass

       @abstractmethod
       def get_or_create_store(self, display_name: str) -> str:
           """
           Get existing store by name or create if doesn't exist.

           Args:
               display_name: Human-readable name for the store

           Returns:
               Store ID/name

           Raises:
               ProviderError: If operation fails
           """
           pass

       @abstractmethod
       def upload_resource(self, resource) -> Dict[str, Any]:
           """
           Upload a JurisdictionResource file to the knowledge store.

           Args:
               resource: JurisdictionResource model instance

           Returns:
               Dict with provider-specific metadata:
               {
                   'file_id': str,          # Provider's file/document ID
                   'store_id': str,         # Provider's store ID
                   'metadata': dict,        # Any additional provider-specific data
               }

           Raises:
               ProviderError: If upload fails

           Side Effects:
               - Updates resource.index_status during upload
               - May create temporary files
           """
           pass

       @abstractmethod
       def remove_resource(self, resource) -> None:
           """
           Remove a resource from the knowledge store.

           Args:
               resource: JurisdictionResource model instance with provider_file_id set

           Raises:
               ProviderError: If removal fails (should not raise on already-deleted)
           """
           pass

       @abstractmethod
       def query(
           self,
           question: str,
           state: Optional[str] = None,
           context: Optional[dict] = None,
           model: Optional[str] = None
       ) -> Dict[str, Any]:
           """
           Query the RAG system with a question.

           Args:
               question: The user's question
               state: Optional state filter (e.g., 'CO', 'GA', 'TN')
               context: Optional conversation context
               model: Optional model override

           Returns:
               Dict with standardized response format:
               {
                   'answer': str,
                   'citations': List[Dict[str, str]],  # [{'source': '...', 'content': '...'}]
                   'state': Optional[str],
                   'provider': str,
                   'model': str,
               }

           Raises:
               ProviderError: If query fails
           """
           pass

       @abstractmethod
       def query_stream(
           self,
           question: str,
           state: Optional[str] = None,
           context: Optional[dict] = None,
           model: Optional[str] = None
       ) -> Generator[Dict[str, Any], None, None]:
           """
           Query the RAG system with streaming response.

           Args:
               question: The user's question
               state: Optional state filter
               context: Optional conversation context
               model: Optional model override

           Yields:
               Dicts with incremental response:
               - {'type': 'chunk', 'text': '...'}
               - {'type': 'citations', 'citations': [...], 'state': '...'}
               - {'type': 'done', 'provider': '...', 'model': '...'}
               - {'type': 'error', 'error': '...'}

           Raises:
               ProviderError: If streaming fails
           """
           pass

       def get_info(self) -> Dict[str, Any]:
           """
           Get provider information and capabilities.

           Returns:
               Dict with provider metadata
           """
           return {
               'provider': self.PROVIDER_NAME,
               'config': self.config,
           }


   class ProviderError(Exception):
       """Base exception for provider errors"""
       pass


   class ProviderConfigError(ProviderError):
       """Configuration error (missing API key, invalid settings)"""
       pass


   class ProviderAPIError(ProviderError):
       """API call failed (rate limit, network error, etc.)"""
       pass
   ```

2. **Create provider factory** (apps/jurisdiction/services/providers/factory.py)
   ```python
   """
   Factory for creating RAG provider instances.
   """
   from django.conf import settings
   from typing import Optional
   import logging

   from .base import RAGProviderBase, ProviderConfigError

   logger = logging.getLogger(__name__)


   class RAGProviderFactory:
       """
       Factory for creating RAG provider instances based on configuration.
       """

       _providers = {}  # Registry of available providers

       @classmethod
       def register_provider(cls, provider_name: str, provider_class):
           """
           Register a provider class.

           Args:
               provider_name: Provider identifier (e.g., 'openai', 'gemini')
               provider_class: Provider class (must inherit from RAGProviderBase)
           """
           cls._providers[provider_name] = provider_class
           logger.info(f"Registered RAG provider: {provider_name}")

       @classmethod
       def get_provider(
           cls,
           provider_name: Optional[str] = None,
           config: Optional[dict] = None
       ) -> RAGProviderBase:
           """
           Get a provider instance by name.

           Args:
               provider_name: Provider to use (defaults to settings.RAG_PROVIDER)
               config: Optional provider-specific configuration

           Returns:
               Provider instance

           Raises:
               ProviderConfigError: If provider not found or invalid
           """
           # Use provided name or fall back to settings
           provider_name = provider_name or getattr(
               settings, 'RAG_PROVIDER', 'openai'
           )

           if provider_name not in cls._providers:
               available = ', '.join(cls._providers.keys())
               raise ProviderConfigError(
                   f"Unknown RAG provider: {provider_name}. "
                   f"Available providers: {available}"
               )

           provider_class = cls._providers[provider_name]

           # Merge config from settings and provided config
           full_config = cls._get_provider_config(provider_name)
           if config:
               full_config.update(config)

           return provider_class(config=full_config)

       @classmethod
       def _get_provider_config(cls, provider_name: str) -> dict:
           """
           Get provider configuration from Django settings.

           Args:
               provider_name: Provider identifier

           Returns:
               Configuration dict for the provider
           """
           config = {}

           if provider_name == 'openai':
               config = {
                   'api_key': settings.OPENAI_API_KEY,
                   'model': getattr(settings, 'OPENAI_MODEL', 'gpt-4.1'),
                   'vector_store_name': getattr(
                       settings, 'OPENAI_VECTOR_STORE_NAME',
                       'StatePublicRecordsStore'
                   ),
                   'real_api_enabled': getattr(
                       settings, 'OPENAI_REAL_API_ENABLED', False
                   ),
               }
           elif provider_name == 'gemini':
               config = {
                   'api_key': settings.GEMINI_API_KEY,
                   'model': getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash'),
                   'store_name': getattr(
                       settings, 'GEMINI_FILE_SEARCH_STORE_NAME',
                       'StatePublicRecordsStore'
                   ),
                   'real_api_enabled': getattr(
                       settings, 'GEMINI_REAL_API_ENABLED', False
                   ),
               }
           elif provider_name == 'mock':
               config = {
                   'real_api_enabled': False,  # Always disabled for mock
               }

           return config

       @classmethod
       def list_providers(cls) -> list:
           """
           List all registered providers.

           Returns:
               List of provider names
           """
           return list(cls._providers.keys())
   ```

3. **Create __init__.py for providers package** (apps/jurisdiction/services/providers/__init__.py)
   ```python
   """
   RAG Provider implementations for FOIA Coach.
   """
   from .base import RAGProviderBase, ProviderError, ProviderConfigError, ProviderAPIError
   from .factory import RAGProviderFactory

   __all__ = [
       'RAGProviderBase',
       'ProviderError',
       'ProviderConfigError',
       'ProviderAPIError',
       'RAGProviderFactory',
   ]
   ```

4. **Test the interface** - Create simple test to verify structure
   ```bash
   # Just verify imports work
   docker compose -f local.yml run --rm foia_coach_api python manage.py shell
   >>> from apps.jurisdiction.services.providers import RAGProviderBase
   >>> from apps.jurisdiction.services.providers import RAGProviderFactory
   ```

#### Deliverables

- [ ] RAGProviderBase abstract class created
- [ ] RAGProviderFactory created
- [ ] Provider exceptions defined
- [ ] Package structure created
- [ ] Import tests pass

**Commit Message:**
```
feat(foia-coach): Add abstract RAG provider interface

- Create RAGProviderBase abstract class with standard contract
- Add RAGProviderFactory for provider instantiation
- Define provider exceptions (ProviderError, ProviderConfigError, ProviderAPIError)
- Establish provider registration system
- Foundation for multi-provider support (OpenAI, Gemini, Mock)

Part of Phase 1: Abstract Provider Interface
```

#### Success Criteria

```bash
# Test imports
docker compose -f local.yml run --rm foia_coach_api python manage.py shell
>>> from apps.jurisdiction.services.providers import RAGProviderBase
>>> from apps.jurisdiction.services.providers import RAGProviderFactory
>>> RAGProviderFactory.list_providers()
[]  # No providers registered yet
```

---

### Phase 2: OpenAI Provider Implementation (60-90 minutes)

**Goal:** Implement OpenAI provider using Vector Stores and Responses API.

**Note:** Largest phase - full OpenAI integration. Uses the simpler Responses API (not Assistants API). Will be the new primary provider.

#### Tasks

1. **Add OpenAI dependency** (requirements.in)
   ```
   # OpenAI
   openai>=1.54.0
   ```

   Then compile:
   ```bash
   docker compose -f local.yml run --rm foia_coach_api pip-compile requirements.in
   docker compose -f local.yml build foia_coach_api
   ```

2. **Create OpenAI provider** (apps/jurisdiction/services/providers/openai_provider.py)
   ```python
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
               vector_store = self.client.beta.vector_stores.create(
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
               vector_stores = self.client.beta.vector_stores.list()
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

               # Update status
               resource.index_status = 'uploading'
               resource.save(update_fields=['index_status'])

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
               self.client.beta.vector_stores.files.create(
                   vector_store_id=store_id,
                   file_id=file_obj.id
               )

               # Wait for file to be processed (poll status)
               import time
               max_wait = 60  # seconds
               elapsed = 0
               while elapsed < max_wait:
                   vector_store_file = self.client.beta.vector_stores.files.retrieve(
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

               logger.info(
                   f"Uploaded resource {resource.id} to vector store: {file_obj.id}"
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
               resource.index_status = 'error'
               resource.save(update_fields=['index_status'])
               raise ProviderAPIError(f"Failed to upload resource: {exc}")

       def remove_resource(self, resource) -> None:
           """Remove a resource from vector store"""
           self._check_api_enabled()

           try:
               if not resource.provider_file_id:
                   logger.warning(
                       f"Resource {resource.id} has no provider_file_id, skipping"
                   )
                   return

               # Delete file from OpenAI
               self.client.files.delete(resource.provider_file_id)
               logger.info(f"Removed resource {resource.id} file: {resource.provider_file_id}")

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
   ```

3. **Register OpenAI provider** (apps/jurisdiction/services/providers/__init__.py)
   ```python
   """
   RAG Provider implementations for FOIA Coach.
   """
   from .base import RAGProviderBase, ProviderError, ProviderConfigError, ProviderAPIError
   from .factory import RAGProviderFactory
   from .openai_provider import OpenAIProvider

   # Register providers
   RAGProviderFactory.register_provider('openai', OpenAIProvider)

   __all__ = [
       'RAGProviderBase',
       'ProviderError',
       'ProviderConfigError',
       'ProviderAPIError',
       'RAGProviderFactory',
       'OpenAIProvider',
   ]
   ```

4. **Add OpenAI settings** (config/settings/base.py)
   ```python
   # OpenAI API Configuration
   OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
   OPENAI_VECTOR_STORE_NAME = os.environ.get(
       'OPENAI_VECTOR_STORE_NAME',
       'StatePublicRecordsStore'
   )
   OPENAI_MODEL = os.environ.get(
       'OPENAI_MODEL',
       'gpt-4.1'  # Latest model with Responses API support
   )

   # Safety flag: Disable real OpenAI API calls by default in development
   OPENAI_REAL_API_ENABLED = os.environ.get(
       'OPENAI_REAL_API_ENABLED', 'false'
   ).lower() in ('true', '1', 'yes')

   # Default RAG provider
   RAG_PROVIDER = os.environ.get('RAG_PROVIDER', 'openai')
   ```

5. **Add environment variables** (.envs/.local/.foia_coach_api)
   ```bash
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_VECTOR_STORE_NAME=StatePublicRecordsStore
   OPENAI_MODEL=gpt-4.1
   OPENAI_REAL_API_ENABLED=false

   # RAG Provider Selection
   RAG_PROVIDER=openai
   ```

6. **Test OpenAI provider** (manual shell test)
   ```bash
   docker compose -f local.yml run --rm foia_coach_api python manage.py shell
   >>> from apps.jurisdiction.services.providers import RAGProviderFactory
   >>> RAGProviderFactory.list_providers()
   ['openai']
   >>> provider = RAGProviderFactory.get_provider('openai')
   >>> provider.PROVIDER_NAME
   'openai'
   ```

#### Deliverables

- [ ] OpenAI SDK added to requirements
- [ ] OpenAIProvider implementation complete
- [ ] Provider registered in factory
- [ ] OpenAI settings added
- [ ] Environment variables documented
- [ ] Basic functionality verified

**Commit Message:**
```
feat(foia-coach): Implement OpenAI RAG provider

- Add OpenAI provider using Vector Stores and Assistants API
- Implement file upload to vector stores
- Implement RAG queries with file search
- Add streaming query support
- Configure OpenAI settings and safety flags
- Register provider in factory

Part of Phase 2: OpenAI Provider Implementation
```

#### Success Criteria

```bash
# Provider registered
>>> RAGProviderFactory.list_providers()
['openai']

# Can create provider (but API disabled by default)
>>> provider = RAGProviderFactory.get_provider('openai')
>>> provider.real_api_enabled
False  # Safety check: API calls disabled by default
```

---

### Phase 3: Refactor Gemini to Provider Pattern (45-60 minutes)

**Goal:** Adapt existing GeminiFileSearchService to match the new provider interface.

**Note:** Preserve all existing Gemini functionality, just wrap it in the new interface.

#### Tasks

1. **Create Gemini provider wrapper** (apps/jurisdiction/services/providers/gemini_provider.py)
   - Copy existing GeminiFileSearchService logic
   - Adapt to implement RAGProviderBase interface
   - Keep all existing functionality (request tracking, MIME types, etc.)
   - Return standardized response format

2. **Register Gemini provider** in factory and __init__.py

3. **Keep old service for backward compatibility** (optional)
   - Can keep apps/jurisdiction/services/gemini_service.py as deprecated
   - Add deprecation warning pointing to new provider system

4. **Test Gemini provider**
   ```bash
   >>> RAGProviderFactory.list_providers()
   ['openai', 'gemini']
   >>> provider = RAGProviderFactory.get_provider('gemini')
   >>> provider.PROVIDER_NAME
   'gemini'
   ```

#### Deliverables

- [ ] GeminiProvider created
- [ ] Registered in factory
- [ ] All Gemini functionality preserved
- [ ] Tests updated to use provider

**Commit Message:**
```
refactor(foia-coach): Adapt Gemini to provider interface

- Create GeminiProvider implementing RAGProviderBase
- Preserve all existing Gemini functionality
- Register Gemini provider in factory
- Add deprecation notice to old service

Part of Phase 3: Refactor Gemini to Provider Pattern
```

---

### Phase 4: Provider Configuration & Selection (30-45 minutes)

**Goal:** Add runtime provider switching and configuration management.

**Note:** Small phase - just configuration plumbing.

#### Tasks

1. **Add provider selection to settings**
   - RAG_PROVIDER environment variable
   - Default to 'openai'
   - Validate provider exists on startup

2. **Create provider configuration helper**
   - Single point to get current provider
   - Caching to avoid repeated initialization
   - Clear error messages for misconfiguration

3. **Add management command to test providers**
   ```bash
   python manage.py test_rag_provider --provider=openai
   python manage.py test_rag_provider --provider=gemini
   ```

#### Deliverables

- [ ] Provider selection configuration
- [ ] Helper utilities for provider access
- [ ] Management command for testing
- [ ] Configuration validated on startup

---

### Phase 5: Update Models & Signals (45-60 minutes)

**Goal:** Make model fields provider-agnostic while maintaining backward compatibility.

**Note:** Database migration required. Careful with existing data.

#### Tasks

1. **Add provider fields to JurisdictionResource model**
   - `provider` - CharField (choices: 'openai', 'gemini', 'mock')
   - `provider_file_id` - Generic file ID (replaces gemini_file_id)
   - `provider_store_id` - Generic store ID
   - `provider_metadata` - JSONField for provider-specific data

2. **Create migration**
   - Add new fields
   - Copy existing gemini_file_id to provider_file_id where provider='gemini'
   - Set default provider based on RAG_PROVIDER setting

3. **Update signals to use provider factory**
   - upload_resource_to_provider (renamed from upload_resource_to_gemini)
   - remove_resource_from_provider (renamed)
   - Use RAGProviderFactory.get_provider()

4. **Backward compatibility**
   - Keep gemini_file_id for now (deprecated)
   - Add property to sync gemini_file_id with provider_file_id

#### Deliverables

- [ ] New provider fields added
- [ ] Migration created and tested
- [ ] Signals updated
- [ ] Backward compatibility maintained

---

### Phase 6: Test Infrastructure & Mocking (45-60 minutes)

**Goal:** Create MockProvider and ensure NO live API calls in tests.

**Note:** Critical for preventing accidental API usage and costs.

#### Tasks

1. **Create MockProvider** (apps/jurisdiction/services/providers/mock_provider.py)
   - Implements RAGProviderBase
   - Returns fake but realistic responses
   - No network calls
   - Configurable behavior for testing different scenarios

2. **Update test configuration** (config/settings/test.py)
   ```python
   # Force mock provider in tests
   RAG_PROVIDER = 'mock'
   OPENAI_REAL_API_ENABLED = False
   GEMINI_REAL_API_ENABLED = False
   ```

3. **Update existing tests**
   - Remove all API mocking
   - Use MockProvider instead
   - Verify no live API calls

4. **Add test for accidental API calls**
   - Test that tries to enable real API in test environment
   - Should fail with clear error

#### Deliverables

- [ ] MockProvider implementation
- [ ] Test settings use mock provider
- [ ] All tests pass without API calls
- [ ] Safety tests added

---

### Phase 7: Management Commands & API Updates (45-60 minutes)

**Goal:** Update management commands and REST API to be provider-aware.

**Note:** User-facing changes - update help text and responses.

#### Tasks

1. **Update management commands**
   - Add --provider flag to all commands
   - Update to use factory
   - Show provider in output

2. **Update API serializers**
   - Add provider field to serializers
   - Return provider info in responses

3. **Update API views**
   - Pass provider selection if needed
   - Include provider stats in responses

4. **Test commands with both providers**

#### Deliverables

- [ ] Commands updated
- [ ] API includes provider info
- [ ] Help text updated
- [ ] Works with all providers

---

### Phase 8: Documentation & Testing (45-60 minutes)

**Goal:** Complete documentation and end-to-end validation.

**Note:** Final polish and verification everything works.

#### Tasks

1. **Update README** with provider information
   - How to select provider
   - Configuration for each provider
   - Comparison table

2. **Create provider comparison guide**
   - Cost comparison
   - Feature comparison
   - When to use each

3. **End-to-end testing**
   - Upload with OpenAI
   - Upload with Gemini
   - Query both providers
   - Compare results
   - Switch providers mid-session

4. **Update API documentation**

5. **Migration guide** for existing deployments

#### Deliverables

- [ ] Complete documentation
- [ ] End-to-end tests pass
- [ ] Migration guide created
- [ ] Ready for production use

---

## Testing Strategy

### Test Levels

1. **Unit Tests** - Provider implementations
   - Use MockProvider
   - Test each method independently
   - No network calls

2. **Integration Tests** - Provider factory
   - Provider registration
   - Configuration loading
   - Provider switching

3. **Manual Tests** - Real APIs (optional)
   - Set REAL_API_ENABLED=true
   - Test with actual OpenAI/Gemini APIs
   - Verify live functionality
   - **NOT run in CI/CD**

### Test Execution

```bash
# All automated tests use MockProvider (no API calls)
docker compose -f local.yml run --rm foia_coach_api pytest

# Manual testing with real OpenAI API (optional, for development only)
OPENAI_REAL_API_ENABLED=true docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=openai

# Manual testing with real Gemini API (optional)
GEMINI_REAL_API_ENABLED=true docker compose -f local.yml run --rm foia_coach_api \
  python manage.py test_rag_provider --provider=gemini
```

---

## Configuration Reference

### Environment Variables

**.envs/.local/.foia_coach_api:**
```bash
# Provider Selection
RAG_PROVIDER=openai  # or 'gemini' or 'mock'

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_VECTOR_STORE_NAME=StatePublicRecordsStore
OPENAI_MODEL=gpt-4o
OPENAI_REAL_API_ENABLED=false

# Gemini Configuration (kept for backward compatibility)
GEMINI_API_KEY=...
GEMINI_FILE_SEARCH_STORE_NAME=StatePublicRecordsStore
GEMINI_MODEL=gemini-1.5-flash
GEMINI_REAL_API_ENABLED=false
```

### Provider Comparison

| Feature | OpenAI | Gemini |
|---------|--------|--------|
| **API Style** | Responses API | Generate Content |
| **Cost (Free Tier)** | Limited free credits | 60 RPM free |
| **Rate Limits** | 500 RPM, 200K TPM | 60 RPM, 2M TPM |
| **Max File Size** | 512 MB | 10 MB |
| **Streaming** | ✅ Native | ✅ Native |
| **Citations** | File annotations | Grounding metadata |
| **Context Window** | 128K tokens (gpt-4.1) | 1M tokens (flash) |

---

## Migration Guide

### For Existing Deployments

1. **Install OpenAI SDK:**
   ```bash
   # Already in requirements.txt after Phase 2
   pip install openai>=1.54.0
   ```

2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Set OpenAI API key:**
   ```bash
   export OPENAI_API_KEY=sk-...
   export OPENAI_REAL_API_ENABLED=true
   ```

4. **Switch provider:**
   ```bash
   export RAG_PROVIDER=openai
   ```

5. **Re-upload resources (optional):**
   - Existing resources will keep Gemini IDs
   - New uploads will use OpenAI
   - To migrate: delete and re-upload resources

### Backward Compatibility

- Existing `gemini_file_id` fields are preserved
- Old Gemini resources continue to work
- Can run mixed environment (some resources in OpenAI, some in Gemini)
- Provider-specific fields allow per-resource provider selection

---

## Success Metrics

### Technical Success
- [ ] All providers implement RAGProviderBase
- [ ] Factory pattern working
- [ ] No live API calls in automated tests
- [ ] All existing tests pass
- [ ] New provider tests pass

### Functional Success
- [ ] Can upload to OpenAI
- [ ] Can query OpenAI
- [ ] Can switch providers via config
- [ ] Streaming works with both providers
- [ ] Citations work with both providers

### Process Success
- [ ] Each phase completes in ~1 hour
- [ ] Clean commits after each phase
- [ ] No breaking changes to existing code
- [ ] Documentation up to date

---

## Risk Mitigation

### API Cost Control

**Risk:** Accidental API usage in tests or development

**Mitigation:**
- REAL_API_ENABLED defaults to False
- MockProvider for all tests
- Clear warnings when API calls disabled
- Request tracking and rate limiting

### Provider Downtime

**Risk:** One provider unavailable

**Mitigation:**
- Support multiple providers
- Can switch providers via config
- Graceful error handling
- Clear error messages

### Migration Complexity

**Risk:** Breaking changes during migration

**Mitigation:**
- Backward compatible model changes
- Keep gemini_* fields during transition
- Gradual migration path
- Rollback plan

---

## Next Steps After Completion

1. **Performance Testing**
   - Compare query latency
   - Compare citation quality
   - Compare costs

2. **Quality Comparison**
   - Test same questions on both providers
   - Evaluate answer quality
   - Evaluate citation relevance

3. **Cost Analysis**
   - Track API costs per provider
   - Calculate cost per query
   - Optimize usage patterns

4. **Additional Providers**
   - Consider Anthropic Claude
   - Consider Azure OpenAI
   - Consider local models (Ollama)

5. **Advanced Features**
   - Multi-provider fallback
   - Automatic provider selection
   - A/B testing framework

---

## Rollback Plan

If provider abstraction causes issues:

1. **Keep old code:** Don't delete gemini_service.py immediately
2. **Feature flag:** Can disable new providers via settings
3. **Database rollback:** Migration is backward compatible
4. **Revert commits:** Each phase is isolated, easy to revert
5. **Gemini still works:** Can always fall back to original implementation

---

## Estimated Timeline

| Phase | Description | Time Estimate | Complexity |
|-------|-------------|---------------|------------|
| Phase 1 | Abstract interface | 45-60 min | Medium |
| Phase 2 | OpenAI provider | 60-90 min | High |
| Phase 3 | Gemini refactor | 45-60 min | Medium |
| Phase 4 | Configuration | 30-45 min | Low |
| Phase 5 | Models & signals | 45-60 min | Medium |
| Phase 6 | Test infrastructure | 45-60 min | Medium |
| Phase 7 | Commands & API | 45-60 min | Medium |
| Phase 8 | Documentation | 45-60 min | Low |
| **Total** | | **6-9 hours** | |

---

## Key Design Decisions

### Why Abstract Provider Pattern?

- **Flexibility:** Easy to add new providers
- **Testability:** MockProvider for testing
- **Isolation:** Provider-specific code separated
- **Maintainability:** Clear contracts and interfaces

### Why OpenAI as Primary Provider?

- **Larger file size limits** (512 MB vs 10 MB)
- **Better rate limits** for free tier
- **Mature API** with good documentation
- **Strong citation support**
- **Higher context window** for future features

### Why Keep Gemini?

- **Already working:** Don't throw away working code
- **Free tier:** Good for development/testing
- **Comparison:** Can evaluate quality differences
- **Redundancy:** Backup if OpenAI has issues

### Why Provider-Agnostic Model?

- **Future-proof:** Easy to add new providers
- **Migration-friendly:** Existing data still works
- **Flexibility:** Can use different providers per resource
- **Clean:** No provider-specific fields proliferating

---

## Additional Resources

### OpenAI Documentation
- Vector Stores: https://platform.openai.com/docs/api-reference/vector-stores
- Assistants API: https://platform.openai.com/docs/assistants/overview
- File Search: https://platform.openai.com/docs/assistants/tools/file-search

### Gemini Documentation
- File Search: https://ai.google.dev/gemini-api/docs/file-search
- Python SDK: https://github.com/googleapis/python-genai

### Design Patterns
- Abstract Factory Pattern
- Strategy Pattern
- Dependency Injection
