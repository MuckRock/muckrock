"""
RAG Provider implementations for FOIA Coach.
"""
from .base import RAGProviderBase, ProviderError, ProviderConfigError, ProviderAPIError
from .factory import RAGProviderFactory
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .mock_provider import MockProvider

# Register providers
RAGProviderFactory.register_provider('openai', OpenAIProvider)
RAGProviderFactory.register_provider('gemini', GeminiProvider)
RAGProviderFactory.register_provider('mock', MockProvider)

__all__ = [
    'RAGProviderBase',
    'ProviderError',
    'ProviderConfigError',
    'ProviderAPIError',
    'RAGProviderFactory',
    'OpenAIProvider',
    'GeminiProvider',
    'MockProvider',
]
