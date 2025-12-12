"""
Management command to create the RAG provider store
"""

# Django
from django.core.management.base import BaseCommand
from django.conf import settings

# Standard Library
import sys

# Local
from apps.jurisdiction.services.providers.helpers import get_provider


class Command(BaseCommand):
    help = "Create or verify the RAG provider store (corpus)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            help="Custom display name for the store (optional)",
        )
        parser.add_argument(
            "--provider",
            type=str,
            help=f"RAG provider to use (default: {settings.RAG_PROVIDER})",
        )

    def handle(self, *args, **options):
        custom_name = options.get("name")
        provider_name = options.get("provider")

        try:
            provider = get_provider(provider_name)

            self.stdout.write(f"Using provider: {provider.PROVIDER_NAME}")

            if custom_name:
                self.stdout.write(
                    f"Creating store with custom name: {custom_name}"
                )
                store_id = provider.create_store(display_name=custom_name)
            else:
                self.stdout.write("Getting or creating provider store...")
                store_id = provider.get_or_create_store()

            self.stdout.write(
                self.style.SUCCESS(f"✓ Store ready: {store_id}")
            )

        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"✗ Failed to create store: {exc}")
            )
            sys.exit(1)
