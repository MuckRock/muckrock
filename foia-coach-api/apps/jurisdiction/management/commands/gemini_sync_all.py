"""
Management command to sync all pending resources to RAG provider
"""

# Django
from django.core.management.base import BaseCommand
from django.conf import settings

# Standard Library
import sys

# Local
from apps.jurisdiction.models import JurisdictionResource
from apps.jurisdiction.services.providers.helpers import get_provider


class Command(BaseCommand):
    help = "Sync all pending jurisdiction resources to RAG provider"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Sync all resources, not just pending ones",
        )
        parser.add_argument(
            "--state",
            type=str,
            help="Sync only resources for a specific state (e.g., CO, GA, TN)",
        )
        parser.add_argument(
            "--provider",
            type=str,
            help=f"RAG provider to use (default: {settings.RAG_PROVIDER})",
        )

    def handle(self, *args, **options):
        sync_all = options.get("all", False)
        state_filter = options.get("state")
        provider_name = options.get("provider")

        try:
            provider = get_provider(provider_name)

            self.stdout.write(f"Using provider: {provider.PROVIDER_NAME}")

            # Build queryset
            queryset = JurisdictionResource.objects.filter(is_active=True)

            if state_filter:
                queryset = queryset.filter(jurisdiction_abbrev=state_filter)

            if not sync_all:
                # Only sync pending or error status
                queryset = queryset.filter(
                    index_status__in=['pending', 'error']
                )

            resources = queryset
            total_count = resources.count()

            if total_count == 0:
                self.stdout.write(
                    self.style.WARNING("No resources to sync")
                )
                return

            self.stdout.write(
                f"Syncing {total_count} resource(s) to {provider.PROVIDER_NAME}..."
            )

            # Sync each resource
            success_count = 0
            error_count = 0

            for resource in resources:
                try:
                    self.stdout.write(
                        f"  - {resource.jurisdiction_abbrev}: "
                        f"{resource.display_name}... ",
                        ending=""
                    )

                    provider.upload_resource(resource)
                    success_count += 1

                    self.stdout.write(self.style.SUCCESS("✓"))

                except Exception as exc:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"✗ {exc}"))

            # Summary
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Sync complete: {success_count} successful, "
                    f"{error_count} errors"
                )
            )

            if error_count > 0:
                sys.exit(1)

        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"✗ Sync failed: {exc}")
            )
            sys.exit(1)
