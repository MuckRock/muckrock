"""
RAG Provider implementations for FOIA Coach.
"""
from .base import RAGProviderBase, ProviderError, ProviderConfigError, ProviderAPIError
from .factory import RAGProviderFactory
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider

# Register providers
RAGProviderFactory.register_provider('openai', OpenAIProvider)
RAGProviderFactory.register_provider('gemini', GeminiProvider)

__all__ = [
    'RAGProviderBase',
    'ProviderError',
    'ProviderConfigError',
    'ProviderAPIError',
    'RAGProviderFactory',
    'OpenAIProvider',
    'GeminiProvider',
]
