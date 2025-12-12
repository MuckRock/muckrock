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
