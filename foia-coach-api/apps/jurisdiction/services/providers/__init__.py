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
