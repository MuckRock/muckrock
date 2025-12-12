"""
Management command to upload a specific resource to RAG provider
"""

# Django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# Standard Library
import sys

# Local
from apps.jurisdiction.models import JurisdictionResource
from apps.jurisdiction.services.providers.helpers import get_provider


class Command(BaseCommand):
    help = "Upload and index a specific jurisdiction resource to RAG provider"

    def add_arguments(self, parser):
        parser.add_argument(
            "resource_id",
            type=int,
            help="ID of the JurisdictionResource to upload",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-upload even if already indexed",
        )
        parser.add_argument(
            "--provider",
            type=str,
            help=f"RAG provider to use (default: {settings.RAG_PROVIDER})",
        )

    def handle(self, *args, **options):
        resource_id = options["resource_id"]
        force = options.get("force", False)
        provider_name = options.get("provider")

        try:
            provider = get_provider(provider_name)

            self.stdout.write(f"Using provider: {provider.PROVIDER_NAME}")

            # Get the resource
            try:
                resource = JurisdictionResource.objects.get(id=resource_id)
            except JurisdictionResource.DoesNotExist:
                raise CommandError(f"JurisdictionResource {resource_id} not found")

            # Check if already indexed
            if resource.index_status == "ready" and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"Resource {resource_id} is already indexed. "
                        f"Use --force to re-upload."
                    )
                )
                return

            self.stdout.write(
                f"Uploading resource {resource_id}: "
                f"{resource.jurisdiction_abbrev} - {resource.display_name}"
            )

            # Upload and index
            provider.upload_resource(resource)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Successfully uploaded and indexed resource {resource_id}"
                )
            )

        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"✗ Failed to upload resource: {exc}")
            )
            sys.exit(1)
