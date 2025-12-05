"""
Management command to sync all pending resources to Gemini
"""

# Django
from django.core.management.base import BaseCommand

# Standard Library
import sys

# Local
from muckrock.jurisdiction.models import JurisdictionResource
from muckrock.jurisdiction.services.gemini_service import GeminiFileSearchService


class Command(BaseCommand):
    help = "Sync all pending jurisdiction resources to Gemini"

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

    def handle(self, *args, **options):
        sync_all = options.get("all", False)
        state_filter = options.get("state")

        try:
            # Build queryset
            queryset = JurisdictionResource.objects.filter(is_active=True)

            if state_filter:
                queryset = queryset.filter(jurisdiction__abbrev=state_filter)

            if not sync_all:
                # Only sync pending or error status
                queryset = queryset.filter(
                    index_status__in=['pending', 'error']
                )

            resources = queryset.select_related('jurisdiction')
            total_count = resources.count()

            if total_count == 0:
                self.stdout.write(
                    self.style.WARNING("No resources to sync")
                )
                return

            self.stdout.write(
                f"Syncing {total_count} resource(s) to Gemini..."
            )

            # Sync each resource
            service = GeminiFileSearchService()
            success_count = 0
            error_count = 0

            for resource in resources:
                try:
                    self.stdout.write(
                        f"  - {resource.jurisdiction.abbrev}: "
                        f"{resource.display_name}... ",
                        ending=""
                    )

                    service.upload_resource(resource)
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
