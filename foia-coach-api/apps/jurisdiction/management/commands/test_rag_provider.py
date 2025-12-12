"""
Management command to test RAG provider configuration and connectivity.
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys

from apps.jurisdiction.services.providers.helpers import (
    get_provider,
    list_available_providers,
    validate_provider_config,
    clear_provider_cache
)
from apps.jurisdiction.services.providers import ProviderConfigError


class Command(BaseCommand):
    help = 'Test RAG provider configuration and connectivity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            help='Provider to test (default: uses RAG_PROVIDER setting)',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available providers',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all available providers',
        )
        parser.add_argument(
            '--query',
            type=str,
            help='Optional test query to run (requires real API enabled)',
        )

    def handle(self, *args, **options):
        # List providers and exit
        if options['list']:
            self._list_providers()
            return

        # Test all providers
        if options['all']:
            self._test_all_providers(options.get('query'))
            return

        # Test specific provider
        provider_name = options.get('provider')
        self._test_provider(provider_name, options.get('query'))

    def _list_providers(self):
        """List all available providers"""
        providers = list_available_providers()
        current = getattr(settings, 'RAG_PROVIDER', 'openai')

        self.stdout.write(self.style.SUCCESS('\nAvailable RAG Providers:'))
        for provider in providers:
            marker = ' (current)' if provider == current else ''
            self.stdout.write(f"  - {provider}{marker}")

        self.stdout.write(f"\nCurrent provider: {current}")
        self.stdout.write(
            f"Set RAG_PROVIDER environment variable to change provider\n"
        )

    def _test_all_providers(self, query=None):
        """Test all available providers"""
        providers = list_available_providers()
        self.stdout.write(
            self.style.SUCCESS(f'\nTesting {len(providers)} providers...\n')
        )

        results = []
        for provider_name in providers:
            success = self._test_provider(provider_name, query, verbose=False)
            results.append((provider_name, success))
            self.stdout.write('')  # Blank line between providers

        # Summary
        self.stdout.write(self.style.SUCCESS('\nSummary:'))
        for provider_name, success in results:
            status = self.style.SUCCESS('✓') if success else self.style.ERROR('✗')
            self.stdout.write(f"  {status} {provider_name}")

    def _test_provider(self, provider_name=None, query=None, verbose=True):
        """Test a specific provider"""
        provider_name = provider_name or getattr(settings, 'RAG_PROVIDER', 'openai')

        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f'\nTesting provider: {provider_name}')
            )
            self.stdout.write('=' * 60)

        try:
            # Clear cache to ensure fresh provider
            clear_provider_cache()

            # Step 1: Validate configuration
            self.stdout.write('\n1. Validating configuration...')
            is_valid, error_msg = validate_provider_config(provider_name)

            if not is_valid:
                self.stdout.write(self.style.ERROR(f'   ✗ Configuration invalid: {error_msg}'))
                return False

            self.stdout.write(self.style.SUCCESS('   ✓ Configuration valid'))

            # Step 2: Get provider instance
            self.stdout.write('\n2. Creating provider instance...')
            provider = get_provider(provider_name, use_cache=False)
            self.stdout.write(self.style.SUCCESS(f'   ✓ Provider created: {provider.PROVIDER_NAME}'))

            # Step 3: Check provider info
            self.stdout.write('\n3. Checking provider info...')
            info = provider.get_info()
            self.stdout.write(f'   Provider: {info["provider"]}')

            config = info.get('config', {})
            self.stdout.write(f'   Model: {config.get("model", "N/A")}')
            self.stdout.write(f'   API Enabled: {config.get("real_api_enabled", False)}')

            if config.get('api_key'):
                masked_key = config['api_key'][:10] + '...' if len(config['api_key']) > 10 else '***'
                self.stdout.write(f'   API Key: {masked_key}')
            else:
                self.stdout.write(self.style.WARNING('   API Key: Not configured'))

            # Step 4: Test store access (if API enabled)
            if config.get('real_api_enabled'):
                self.stdout.write('\n4. Testing store access...')
                try:
                    store_id = provider.get_or_create_store()
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Store accessible: {store_id}'))
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f'   ✗ Store access failed: {exc}'))
                    return False
            else:
                self.stdout.write('\n4. Testing store access...')
                self.stdout.write(
                    self.style.WARNING('   ⊘ Skipped (API disabled - set REAL_API_ENABLED=true to test)')
                )

            # Step 5: Test query (if requested and API enabled)
            if query:
                if config.get('real_api_enabled'):
                    self.stdout.write(f'\n5. Testing query: "{query}"...')
                    try:
                        result = provider.query(question=query)
                        self.stdout.write(self.style.SUCCESS('   ✓ Query successful'))
                        self.stdout.write(f'   Answer length: {len(result["answer"])} chars')
                        self.stdout.write(f'   Citations: {len(result.get("citations", []))}')
                        if verbose:
                            self.stdout.write(f'\n   Answer: {result["answer"][:200]}...')
                    except Exception as exc:
                        self.stdout.write(self.style.ERROR(f'   ✗ Query failed: {exc}'))
                        return False
                else:
                    self.stdout.write('\n5. Testing query...')
                    self.stdout.write(
                        self.style.WARNING('   ⊘ Skipped (API disabled)')
                    )

            # Success
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Provider {provider_name} is working correctly!\n')
                )
            return True

        except ProviderConfigError as exc:
            self.stdout.write(self.style.ERROR(f'\n✗ Configuration Error: {exc}\n'))
            return False
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'\n✗ Unexpected Error: {exc}\n'))
            if verbose:
                import traceback
                self.stdout.write(traceback.format_exc())
            return False
