"""
Management command to export jurisdiction data as Markdown
"""

# Django
from django.core.management.base import BaseCommand

# Standard Library
import os

# MuckRock
from muckrock.jurisdiction.markdown_export import jurisdiction_to_markdown
from muckrock.jurisdiction.models import Jurisdiction


class Command(BaseCommand):
    """Export jurisdiction pages as Markdown files"""

    help = "Export jurisdiction data to Markdown format"

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            help="Export a specific jurisdiction by slug",
        )
        parser.add_argument(
            "--ids",
            help="Export specific jurisdictions by ID (comma-separated)",
        )
        parser.add_argument(
            "--output",
            default="markdown/jurisdictions/",
            help="Output directory or file path (default: markdown/jurisdictions/)",
        )
        parser.add_argument(
            "--single-file",
            action="store_true",
            help="Export all jurisdictions to a single file",
        )
        parser.add_argument(
            "--include-federal",
            action="store_true",
            help="Include federal jurisdiction (default: states only)",
        )
        parser.add_argument(
            "--no-stats",
            action="store_true",
            help="Skip statistics for faster export",
        )
        parser.add_argument(
            "--no-requests",
            action="store_true",
            help="Skip recent requests for faster export",
        )
        parser.add_argument(
            "--base-url",
            default="https://www.muckrock.com",
            help=(
                "Base URL for generating absolute links "
                "(default: https://www.muckrock.com)"
            ),
        )

    def handle(self, *args, **options):
        # Determine which jurisdictions to export
        queryset = self._get_queryset(options)

        # Optimize query with select_related and prefetch_related
        queryset = queryset.select_related(
            "parent", "law", "jurisdictionpage"
        ).prefetch_related("law__years", "holidays")

        if not queryset.exists():
            self.stdout.write(
                self.style.WARNING("No jurisdictions found matching criteria.")
            )
            return

        # Export options
        include_stats = not options["no_stats"]
        include_requests = not options["no_requests"]
        base_url = options["base_url"]

        # Single file or multiple files?
        if options["single_file"]:
            self._export_single_file(
                queryset, options["output"], include_stats, include_requests, base_url
            )
        else:
            self._export_multiple_files(
                queryset, options["output"], include_stats, include_requests, base_url
            )

    def _get_queryset(self, options):
        """Build the queryset based on command options"""
        queryset = Jurisdiction.objects.filter(hidden=False)

        # Filter by slug
        if options["slug"]:
            return queryset.filter(slug=options["slug"])

        # Filter by IDs
        if options["ids"]:
            ids = [int(id.strip()) for id in options["ids"].split(",")]
            return queryset.filter(id__in=ids)

        # Default: states only (or include federal if specified)
        if options["include_federal"]:
            return queryset.filter(level__in=["s", "f"])
        else:
            return queryset.filter(level="s")

    def _export_single_file(
        self, queryset, output_path, include_stats, include_requests, base_url
    ):
        """Export all jurisdictions to a single Markdown file"""
        # Default filename if output is a directory
        if output_path.endswith("/"):
            output_path = os.path.join(output_path, "jurisdictions.md")
        elif os.path.isdir(output_path):
            output_path = os.path.join(output_path, "jurisdictions.md")

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        self.stdout.write(
            f"Exporting {queryset.count()} jurisdictions to {output_path}..."
        )

        # Generate Markdown for all jurisdictions
        markdown_sections = []
        for jurisdiction in queryset:
            self.stdout.write(f"  Processing {jurisdiction.name}...")
            markdown = jurisdiction_to_markdown(
                jurisdiction,
                include_stats=include_stats,
                include_requests=include_requests,
                base_url=base_url,
            )
            markdown_sections.append(markdown)

        # Combine with page breaks
        combined_markdown = "\n\n" + "=" * 80 + "\n\n".join(markdown_sections)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(combined_markdown)

        success_msg = (
            f"Successfully exported {queryset.count()} jurisdictions "
            f"to {output_path}"
        )
        self.stdout.write(self.style.SUCCESS(success_msg))

    def _export_multiple_files(
        self, queryset, output_dir, include_stats, include_requests, base_url
    ):
        """Export each jurisdiction to its own Markdown file"""
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        self.stdout.write(
            f"Exporting {queryset.count()} jurisdictions to {output_dir}..."
        )

        exported_count = 0
        for jurisdiction in queryset:
            self.stdout.write(f"  Processing {jurisdiction.name}...")

            # Generate Markdown
            markdown = jurisdiction_to_markdown(
                jurisdiction,
                include_stats=include_stats,
                include_requests=include_requests,
                base_url=base_url,
            )

            # Write to file
            filename = f"{jurisdiction.slug}.md"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as output_file:
                output_file.write(markdown)

            self.stdout.write(f"    Wrote {filepath}")
            exported_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully exported {exported_count} jurisdictions to {output_dir}"
            )
        )
