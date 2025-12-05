"""
Management command to upload a specific resource to Gemini
"""

# Django
from django.core.management.base import BaseCommand, CommandError

# Standard Library
import sys

# Local
from muckrock.jurisdiction.models import JurisdictionResource
from muckrock.jurisdiction.services.gemini_service import GeminiFileSearchService


class Command(BaseCommand):
    help = "Upload and index a specific jurisdiction resource to Gemini"

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

    def handle(self, *args, **options):
        resource_id = options["resource_id"]
        force = options.get("force", False)

        try:
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
                f"{resource.jurisdiction.name} - {resource.display_name}"
            )

            # Upload and index
            service = GeminiFileSearchService()
            service.upload_resource(resource)

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
