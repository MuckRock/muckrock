"""
Management command to create the Gemini File Search store
"""

# Django
from django.core.management.base import BaseCommand

# Standard Library
import sys

# Local
from apps.jurisdiction.services.gemini_service import GeminiFileSearchService


class Command(BaseCommand):
    help = "Create or verify the Gemini File Search store (corpus)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            help="Custom display name for the store (optional)",
        )

    def handle(self, *args, **options):
        custom_name = options.get("name")

        try:
            service = GeminiFileSearchService()

            if custom_name:
                self.stdout.write(
                    f"Creating Gemini store with custom name: {custom_name}"
                )
                corpus_name = service.create_store(display_name=custom_name)
            else:
                self.stdout.write("Getting or creating Gemini store...")
                corpus_name = service.get_or_create_store()

            self.stdout.write(
                self.style.SUCCESS(f"✓ Store ready: {corpus_name}")
            )

        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"✗ Failed to create store: {exc}")
            )
            sys.exit(1)
