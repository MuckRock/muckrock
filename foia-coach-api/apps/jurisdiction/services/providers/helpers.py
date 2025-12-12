"""
Helper utilities for RAG provider management.
"""
from django.conf import settings
from typing import Optional
import logging

from .factory import RAGProviderFactory
from .base import RAGProviderBase, ProviderConfigError

logger = logging.getLogger(__name__)


# Module-level cache for provider instances
_provider_cache = {}


def get_provider(provider_name: Optional[str] = None, use_cache: bool = True) -> RAGProviderBase:
    """
    Get a RAG provider instance with optional caching.

    This is the recommended way to get a provider instance in application code.
    Provides caching to avoid repeated initialization and clear error messages.

    Args:
        provider_name: Provider to use (defaults to settings.RAG_PROVIDER)
        use_cache: Whether to use cached provider instance (default: True)

    Returns:
        Provider instance

    Raises:
        ProviderConfigError: If provider not found or invalid configuration

    Example:
        >>> from apps.jurisdiction.services.providers.helpers import get_provider
        >>> provider = get_provider()  # Uses settings.RAG_PROVIDER
        >>> provider = get_provider('gemini')  # Explicitly use Gemini
    """
    # Use provided name or fall back to settings
    provider_name = provider_name or getattr(settings, 'RAG_PROVIDER', 'openai')

    # Check cache first
    if use_cache and provider_name in _provider_cache:
        logger.debug(f"Using cached provider: {provider_name}")
        return _provider_cache[provider_name]

    # Create provider
    try:
        provider = RAGProviderFactory.get_provider(provider_name)

        # Cache the instance
        if use_cache:
            _provider_cache[provider_name] = provider
            logger.debug(f"Cached new provider: {provider_name}")

        return provider

    except ProviderConfigError as exc:
        # Add helpful context to error message
        available = ', '.join(RAGProviderFactory.list_providers())
        logger.error(
            f"Failed to get provider '{provider_name}': {exc}. "
            f"Available providers: {available}"
        )
        raise ProviderConfigError(
            f"Failed to get provider '{provider_name}': {exc}\n"
            f"Available providers: {available}\n"
            f"Check your RAG_PROVIDER setting in environment variables."
        )


def clear_provider_cache():
    """
    Clear the provider cache.

    Useful for testing or when provider configuration changes at runtime.
    """
    global _provider_cache
    _provider_cache = {}
    logger.info("Provider cache cleared")


def get_provider_info(provider_name: Optional[str] = None) -> dict:
    """
    Get information about a provider without creating a full instance.

    Args:
        provider_name: Provider to query (defaults to settings.RAG_PROVIDER)

    Returns:
        Dict with provider information

    Raises:
        ProviderConfigError: If provider not found
    """
    provider = get_provider(provider_name, use_cache=True)
    return provider.get_info()


def list_available_providers() -> list:
    """
    List all registered providers.

    Returns:
        List of provider names
    """
    return RAGProviderFactory.list_providers()


def validate_provider_config(provider_name: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Validate provider configuration.

    Args:
        provider_name: Provider to validate (defaults to settings.RAG_PROVIDER)

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid
    """
    provider_name = provider_name or getattr(settings, 'RAG_PROVIDER', 'openai')

    try:
        # Try to create provider
        provider = get_provider(provider_name, use_cache=False)

        # Check if it has required attributes
        if not hasattr(provider, 'PROVIDER_NAME'):
            return False, f"Provider '{provider_name}' missing PROVIDER_NAME attribute"

        if provider.PROVIDER_NAME != provider_name:
            return False, (
                f"Provider name mismatch: expected '{provider_name}', "
                f"got '{provider.PROVIDER_NAME}'"
            )

        # Validate configuration
        config = provider.config
        if not config:
            return False, f"Provider '{provider_name}' has no configuration"

        # Provider-specific validation
        if provider_name == 'openai':
            if not config.get('api_key'):
                return False, "OpenAI provider missing API key (OPENAI_API_KEY)"
            if not config.get('real_api_enabled'):
                logger.warning(
                    "OpenAI provider API is disabled (OPENAI_REAL_API_ENABLED=false)"
                )

        elif provider_name == 'gemini':
            if not config.get('api_key'):
                return False, "Gemini provider missing API key (GEMINI_API_KEY)"
            if not config.get('real_api_enabled'):
                logger.warning(
                    "Gemini provider API is disabled (GEMINI_REAL_API_ENABLED=false)"
                )

        return True, None

    except ProviderConfigError as exc:
        return False, str(exc)
    except Exception as exc:
        logger.error(f"Unexpected error validating provider: {exc}", exc_info=True)
        return False, f"Unexpected error: {exc}"
