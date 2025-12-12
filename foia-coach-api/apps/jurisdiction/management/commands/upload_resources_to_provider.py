"""
Management command to upload jurisdiction resources to a specific provider.

This command creates ResourceProviderUpload records with status='pending',
which triggers the signal handlers to perform the actual uploads.
"""
# Django
from django.core.management.base import BaseCommand, CommandError

# Local
from apps.jurisdiction.models import JurisdictionResource, ResourceProviderUpload


class Command(BaseCommand):
    help = 'Upload jurisdiction resources to a specific provider'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            required=True,
            choices=['openai', 'gemini', 'mock'],
            help='Provider to upload resources to'
        )
        parser.add_argument(
            '--state',
            help='Filter by jurisdiction abbreviation (e.g., CO, GA, TN)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-upload even if already uploaded (resets status to pending)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be uploaded without actually creating uploads'
        )

    def handle(self, *args, **options):
        provider = options['provider']
        state = options.get('state')
        force = options['force']
        dry_run = options['dry_run']

        # Build queryset for resources
        queryset = JurisdictionResource.objects.filter(is_active=True)

        if state:
            queryset = queryset.filter(jurisdiction_abbrev=state)
            self.stdout.write(f"Filtering resources for state: {state}")

        resource_count = queryset.count()

        if resource_count == 0:
            raise CommandError("No active resources found with the given filters")

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {resource_count} active resource(s) to upload to {provider}"
            )
        )

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
            for resource in queryset:
                # Check if upload already exists
                existing = resource.get_upload_status(provider)
                if existing:
                    status_msg = f"(existing: {existing.index_status})"
                else:
                    status_msg = "(new upload)"

                self.stdout.write(
                    f"  - {resource.jurisdiction_abbrev}: {resource.display_name} {status_msg}"
                )
            return

        # Create or update upload records
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for resource in queryset:
            # Check if upload already exists
            existing = resource.get_upload_status(provider)

            if existing:
                if force or existing.index_status in ['error', 'not_uploaded']:
                    # Reset to pending to retry
                    existing.index_status = 'pending'
                    existing.error_message = ''
                    existing.save(update_fields=['index_status', 'error_message', 'updated_at'])
                    updated_count += 1
                    self.stdout.write(
                        f"  ✓ Reset {resource.jurisdiction_abbrev}: {resource.display_name} "
                        f"to pending (was {existing.index_status})"
                    )
                else:
                    # Skip if already uploaded successfully
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⊘ Skipped {resource.jurisdiction_abbrev}: {resource.display_name} "
                            f"(already {existing.index_status}). Use --force to re-upload."
                        )
                    )
            else:
                # Create new upload record
                upload = ResourceProviderUpload.objects.create(
                    resource=resource,
                    provider=provider,
                    index_status='pending'
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Created upload for {resource.jurisdiction_abbrev}: "
                        f"{resource.display_name}"
                    )
                )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Upload Summary:"))
        self.stdout.write(f"  Created:  {created_count}")
        self.stdout.write(f"  Updated:  {updated_count}")
        self.stdout.write(f"  Skipped:  {skipped_count}")
        self.stdout.write(f"  Total:    {resource_count}")
        self.stdout.write("=" * 60)

        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nUploads will be processed by signal handlers. "
                    "Check the admin interface or logs to monitor progress."
                )
            )
