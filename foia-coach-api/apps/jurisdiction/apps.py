"""
Jurisdiction app configuration.
"""
from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class JurisdictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.jurisdiction'
    verbose_name = 'Jurisdiction Resources'

    def ready(self):
        # Import signals when app is ready
        import apps.jurisdiction.signals  # noqa

        # Validate RAG provider configuration on startup
        self._validate_provider_config()

    def _validate_provider_config(self):
        """Validate RAG provider configuration on app startup"""
        try:
            from apps.jurisdiction.services.providers.helpers import (
                validate_provider_config,
                list_available_providers
            )

            provider_name = getattr(settings, 'RAG_PROVIDER', 'openai')
            is_valid, error_msg = validate_provider_config(provider_name)

            if is_valid:
                logger.info(
                    f"✓ RAG provider '{provider_name}' configured successfully"
                )
            else:
                available = ', '.join(list_available_providers())
                logger.error(
                    f"✗ RAG provider '{provider_name}' configuration error: {error_msg}\n"
                    f"  Available providers: {available}\n"
                    f"  Check your RAG_PROVIDER setting in environment variables."
                )

        except Exception as exc:
            # Don't crash on startup - just log the error
            logger.error(
                f"Failed to validate RAG provider configuration: {exc}",
                exc_info=True
            )
