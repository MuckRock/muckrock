"""
Management command to test queries against the Gemini RAG system
"""

# Django
from django.core.management.base import BaseCommand

# Standard Library
import sys

# Local
from muckrock.jurisdiction.services.gemini_service import GeminiFileSearchService


class Command(BaseCommand):
    help = "Test a query against the Gemini RAG system"

    def add_arguments(self, parser):
        parser.add_argument(
            "question",
            type=str,
            help="The question to ask",
        )
        parser.add_argument(
            "--state",
            type=str,
            help="Filter by state (e.g., CO, GA, TN)",
        )
        parser.add_argument(
            "--stream",
            action="store_true",
            help="Use streaming response",
        )

    def handle(self, *args, **options):
        question = options["question"]
        state = options.get("state")
        use_stream = options.get("stream", False)

        try:
            service = GeminiFileSearchService()

            self.stdout.write(f"Question: {question}")
            if state:
                self.stdout.write(f"State filter: {state}")
            self.stdout.write("")

            if use_stream:
                # Streaming response
                self.stdout.write("Answer (streaming):")
                self.stdout.write("-" * 60)

                citations = []
                for chunk in service.query_stream(question, state=state):
                    if chunk['type'] == 'chunk':
                        self.stdout.write(chunk['text'], ending="")
                        self.stdout.flush()
                    elif chunk['type'] == 'citations':
                        citations = chunk['citations']
                    elif chunk['type'] == 'error':
                        self.stdout.write(
                            self.style.ERROR(f"\n\n✗ Error: {chunk['error']}")
                        )
                        sys.exit(1)

                self.stdout.write("")
                self.stdout.write("-" * 60)

                # Display citations
                if citations:
                    self.stdout.write("\nCitations:")
                    for i, citation in enumerate(citations, 1):
                        self.stdout.write(
                            f"  [{i}] {citation['display_name']}"
                        )
                        self.stdout.write(f"      {citation['source']}")
                else:
                    self.stdout.write("\nNo citations available")

            else:
                # Regular response
                result = service.query(question, state=state)

                self.stdout.write("Answer:")
                self.stdout.write("-" * 60)
                self.stdout.write(result['answer'])
                self.stdout.write("-" * 60)

                # Display citations
                if result['citations']:
                    self.stdout.write("\nCitations:")
                    for i, citation in enumerate(result['citations'], 1):
                        self.stdout.write(
                            f"  [{i}] {citation['display_name']}"
                        )
                        self.stdout.write(f"      {citation['source']}")
                else:
                    self.stdout.write("\nNo citations available")

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✓ Query complete"))

        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"✗ Query failed: {exc}")
            )
            sys.exit(1)
