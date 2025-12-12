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
